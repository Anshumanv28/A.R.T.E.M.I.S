"""
Agent tools: central registry and optional RAG tool registration helper.
"""

from artemis.agent.tools.registry import ToolDescriptor, ToolRegistry

__all__ = ["ToolDescriptor", "ToolRegistry", "build_rag_registry"]


def build_rag_registry(retriever, indexer=None, default_k: int = 5):
    """
    Build a ToolRegistry with RAG tools: search_documents (requires retriever), ingest_file (if indexer provided), and collection management.

    Args:
        retriever: Retriever instance for search_documents.
        indexer: Optional Indexer for ingest_file; if None, ingest_file is not registered.
        default_k: Default number of documents for search_documents.

    Returns:
        ToolRegistry with RAG tools registered; all callables accept **kwargs.
    """
    from artemis.rag.tools import (
        create_rag_ingest_tool,
        create_rag_ingest_directory_tool,
        list_collections_tool,
        get_collection_info_tool,
        create_collection_tool,
        clear_collection_tool,
        delete_collection_tool,
    )

    registry = ToolRegistry()

    def search_documents(**kwargs):
        q = kwargs.get("query", "")
        k = kwargs.get("k", default_k)
        return retriever.retrieve(q, k=k)

    registry.register(
        "search_documents",
        search_documents,
        description="Search the knowledge base for relevant documents. Returns a list of {text, score, metadata}.",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "k": {"type": "integer", "description": "Number of documents to return", "default": default_k},
            },
            "required": ["query"],
        },
    )

    if indexer is not None:
        ingest_fn = create_rag_ingest_tool(indexer)

        def ingest_file_kw(**kwargs):
            path = kwargs.get("path", "")
            file_type = kwargs.get("file_type", "text")
            return ingest_fn(path, file_type)

        registry.register(
            "ingest_file",
            ingest_file_kw,
            description="Ingest a file into the knowledge base. file_type: csv, pdf, docx, md, text.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "file_type": {"type": "string", "enum": ["csv", "pdf", "docx", "md", "text"]},
                },
                "required": ["path", "file_type"],
            },
        )

        ingest_dir_fn = create_rag_ingest_directory_tool(indexer, default_extension="md")

        def ingest_directory_kw(**kwargs):
            dir_path = kwargs.get("directory_path", "")
            ext = kwargs.get("file_extension", "md")
            return ingest_dir_fn(dir_path, ext)

        registry.register(
            "ingest_directory",
            ingest_directory_kw,
            description="Ingest all files in a directory (e.g. RAG_demo/techcorp_docs). file_extension: md, pdf, txt, etc.; default md.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string"},
                    "file_extension": {"type": "string", "default": "md"},
                },
                "required": ["directory_path"],
            },
        )

    def list_coll(**kwargs):
        return list_collections_tool()

    registry.register(
        "list_collections",
        list_coll,
        description="List all Qdrant collection names.",
        parameters_schema={"type": "object", "properties": {}},
    )

    def get_info(**kwargs):
        return get_collection_info_tool(kwargs.get("collection_name", ""))

    registry.register(
        "get_collection_info",
        get_info,
        description="Get information about a collection (points count, status).",
        parameters_schema={
            "type": "object",
            "properties": {"collection_name": {"type": "string"}},
            "required": ["collection_name"],
        },
    )

    def create_coll(**kwargs):
        return create_collection_tool(
            kwargs.get("collection_name", ""),
            embedding_dim=kwargs.get("embedding_dim"),
        )

    registry.register(
        "create_collection",
        create_coll,
        description="Create a new Qdrant collection.",
        parameters_schema={
            "type": "object",
            "properties": {
                "collection_name": {"type": "string"},
                "embedding_dim": {"type": "integer"},
            },
            "required": ["collection_name"],
        },
    )

    def clear_coll(**kwargs):
        return clear_collection_tool(
            kwargs.get("collection_name", ""),
            confirm=kwargs.get("confirm", False),
        )

    registry.register(
        "clear_collection",
        clear_coll,
        description="Clear all points from a collection. Requires confirm=True.",
        parameters_schema={
            "type": "object",
            "properties": {
                "collection_name": {"type": "string"},
                "confirm": {"type": "boolean", "default": False},
            },
            "required": ["collection_name"],
        },
    )

    def delete_coll(**kwargs):
        return delete_collection_tool(
            kwargs.get("collection_name", ""),
            confirm=kwargs.get("confirm", False),
        )

    registry.register(
        "delete_collection",
        delete_coll,
        description="Delete a collection entirely. Requires confirm=True.",
        parameters_schema={
            "type": "object",
            "properties": {
                "collection_name": {"type": "string"},
                "confirm": {"type": "boolean", "default": False},
            },
            "required": ["collection_name"],
        },
    )

    return registry
