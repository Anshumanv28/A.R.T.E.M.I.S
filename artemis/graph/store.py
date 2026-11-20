"""
Neo4j-backed entity/relationship store for GraphRAG.

Schema: a single (:Entity {tenant_id, name, type}) label and a single
generic (:Entity)-[:RELATES_TO {relation, source_doc}]->(:Entity) relationship
type, with the actual verb phrase ("manages", "uses", ...) stored as the
`relation` property rather than as distinct dynamic relationship types.
Simpler to query (no APOC needed for dynamic relationship types) at the
cost of not using Neo4j's native relationship-type indexing -- fine at
the scale this is meant for.

Tenant isolation is property-based (every node/relationship carries
tenant_id and every query filters by it), not separate Neo4j databases --
AuraDB's free tier only provides one database, so this is the only option,
and it mirrors the same isolation principle used for Qdrant collections
in artemis/auth.py.
"""

from typing import Any, Dict, List, Optional

from artemis.utils import get_logger

logger = get_logger(__name__)

RELATIONSHIP_TYPE = "RELATES_TO"


def _format_path(path) -> Dict[str, Any]:
    """
    A neo4j Path -> {text, entities, source_docs, hops} for use as a retrieval result.

    The traversal query matches relationships in either direction (undirected
    "-[:RELATES_TO*1..N]-"), so path.nodes[i]/[i+1] reflect *traversal* order,
    not necessarily the relationship's actual stored direction. Reading the
    triple off traversal order alone can silently reverse its meaning (e.g.
    a stored "Team Alpha reports_to Director Sarah" edge, traversed starting
    from Director Sarah, would read as "Director Sarah reports_to Team Alpha"
    -- backward). Each relationship's own start_node/end_node is checked so
    the printed subject/object always match how it was actually stored.
    """
    nodes = list(path.nodes)
    rels = list(path.relationships)
    triples = []
    for i, rel in enumerate(rels):
        node_a, node_b = nodes[i], nodes[i + 1]
        if rel.start_node.element_id == node_a.element_id:
            subject, obj = node_a, node_b
        else:
            subject, obj = node_b, node_a
        relation = rel.get("relation") or rel.type
        triples.append(f"{subject.get('name', '?')} {relation} {obj.get('name', '?')}")
    source_docs = sorted({rel.get("source_doc") for rel in rels if rel.get("source_doc")})
    return {
        "text": "; ".join(triples),
        "entities": [n.get("name") for n in nodes],
        "source_docs": source_docs,
        "hops": len(rels),
    }


class GraphStore:
    """Entity/relationship CRUD + traversal, scoped per tenant_id."""

    def __init__(self, driver):
        self.driver = driver
        self._ensure_constraints()

    def _ensure_constraints(self) -> None:
        try:
            with self.driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT entity_tenant_name IF NOT EXISTS "
                    "FOR (e:Entity) REQUIRE (e.tenant_id, e.name) IS UNIQUE"
                )
        except Exception as e:
            logger.warning(f"Could not create Entity uniqueness constraint (continuing without it): {e}")

    def upsert_graph(
        self,
        tenant_id: str,
        entities: List[Dict[str, str]],
        relationships: List[Dict[str, str]],
        source_doc: str,
    ) -> None:
        """Idempotently merge entities/relationships -- re-ingesting the same document won't create duplicates."""
        if not entities:
            return
        with self.driver.session() as session:
            session.execute_write(self._upsert_graph_tx, tenant_id, entities, relationships, source_doc)

    @staticmethod
    def _upsert_graph_tx(tx, tenant_id: str, entities, relationships, source_doc) -> None:
        for e in entities:
            tx.run(
                "MERGE (n:Entity {tenant_id: $tenant_id, name: $name}) "
                "SET n.type = $type, n.last_seen_doc = $source_doc",
                tenant_id=tenant_id,
                name=e["name"],
                type=e.get("type", "Other"),
                source_doc=source_doc,
            )
        for r in relationships:
            tx.run(
                f"""
                MATCH (a:Entity {{tenant_id: $tenant_id, name: $source}})
                MATCH (b:Entity {{tenant_id: $tenant_id, name: $target}})
                MERGE (a)-[rel:{RELATIONSHIP_TYPE} {{relation: $relation}}]->(b)
                SET rel.source_doc = $source_doc
                """,
                tenant_id=tenant_id,
                source=r["source"],
                target=r["target"],
                relation=r["relation"],
                source_doc=source_doc,
            )

    def find_matching_entities(self, tenant_id: str, query: str, limit: int = 10) -> List[str]:
        """
        Heuristic entity-linking: entities where any word of the entity's
        name (longer than 2 chars, to skip noise like "of"/"to") appears in
        the query. Word-level rather than whole-name substring matching,
        since a query referring to "Sarah" should still match an entity
        named "Director Sarah". Simple on purpose -- a dedicated NER pass
        over the query would be more accurate but is more than this needs to
        prove the mechanism; see artemis/graph/extraction.py's docstring for
        the same tradeoff on the ingestion side.
        """
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {tenant_id: $tenant_id}) "
                "WHERE ANY(word IN split(e.name, ' ') WHERE size(word) > 2 "
                "AND toLower($search_text) CONTAINS toLower(word)) "
                "RETURN e.name AS name LIMIT $limit",
                tenant_id=tenant_id,
                search_text=query,
                limit=limit,
            )
            return [record["name"] for record in result]

    def traverse(
        self,
        tenant_id: str,
        entity_names: List[str],
        max_hops: int = 2,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Paths of up to max_hops from any of entity_names to any other entity in the same tenant's graph."""
        if not entity_names:
            return []
        with self.driver.session() as session:
            result = session.run(
                f"MATCH path = (start:Entity {{tenant_id: $tenant_id}})"
                f"-[:{RELATIONSHIP_TYPE}*1..{int(max_hops)}]-"
                f"(end:Entity {{tenant_id: $tenant_id}}) "
                "WHERE start.name IN $names "
                "RETURN path LIMIT $limit",
                tenant_id=tenant_id,
                names=entity_names,
                limit=limit,
            )
            return [_format_path(record["path"]) for record in result]

    def delete_tenant_graph(self, tenant_id: str) -> None:
        """Remove all of one tenant's nodes/relationships (used by tests; not exposed as an agent tool)."""
        with self.driver.session() as session:
            session.run("MATCH (e:Entity {tenant_id: $tenant_id}) DETACH DELETE e", tenant_id=tenant_id)

    def close(self) -> None:
        self.driver.close()


__all__ = ["GraphStore", "RELATIONSHIP_TYPE"]
