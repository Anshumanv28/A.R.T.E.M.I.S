"""
Agent tools: central registry and optional RAG tool registration helper.
"""

from artemis.agent.tools.registry import ToolDescriptor, ToolRegistry

__all__ = ["ToolDescriptor", "ToolRegistry", "build_rag_registry"]


def build_rag_registry(
    retriever,
    indexer=None,
    default_k: int = 5,
    retrievers=None,
    llm_client_for_agentic=None,
    indexers=None,
    retrievers_by_collection=None,
    default_collection=None,
):
    """
    Build a ToolRegistry with RAG tools: search_documents (requires retriever or retrievers), ingest_file (if indexer or indexers provided), and collection management.

    Args:
        retriever: Retriever instance for search_documents (used when retrievers/retrievers_by_collection is None).
        indexer: Optional Indexer for ingest_file (single-collection mode); if None and indexers is None, ingest_file is not registered.
        default_k: Default number of documents for search_documents.
        retrievers: Optional dict mapping search_mode (str) -> Retriever (single-collection). If provided, search_documents uses search_mode to pick retriever.
        llm_client_for_agentic: Optional LLM client for agentic chunking.
        indexers: Optional dict mapping collection_name -> Indexer. When set with retrievers_by_collection, search and ingest accept collection_name to switch collections.
        retrievers_by_collection: Optional dict mapping collection_name -> { search_mode -> Retriever }. When set with indexers, search_documents uses collection_name then search_mode.
        default_collection: Default collection when using indexers/retrievers_by_collection (e.g. "artemis_user_docs"). Used when the agent omits collection_name.

    Returns:
        ToolRegistry with RAG tools registered; all callables accept **kwargs.
    """
    from artemis.rag.tools import (
        create_rag_ingest_tool,
        create_rag_ingest_directory_tool,
        suggest_ingest_options,
        list_collections_tool,
        get_collection_info_tool,
        create_collection_tool,
        clear_collection_tool,
        delete_collection_tool,
    )

    registry = ToolRegistry()
    multi_collection = indexers is not None and retrievers_by_collection is not None and len(indexers) > 0 and len(retrievers_by_collection) > 0
    collection_enum = sorted(indexers.keys()) if multi_collection else None
    default_coll = default_collection or (list(indexers.keys())[0] if indexers else None)

    # Resolve search: multi-collection -> collection_name + mode; single retrievers dict -> mode; else single retriever
    if multi_collection:
        first_retrievers = next(iter(retrievers_by_collection.values()), {})
        search_mode_enum = sorted(first_retrievers.keys()) if first_retrievers else ["semantic"]
        default_mode = "semantic" if "semantic" in search_mode_enum else (search_mode_enum[0] if search_mode_enum else "semantic")

        def search_documents(**kwargs):
            q = kwargs.get("query", "")
            k = kwargs.get("k", default_k)
            mode = kwargs.get("search_mode", default_mode)
            coll = kwargs.get("collection_name") or default_coll
            by_mode = retrievers_by_collection.get(coll)
            if not by_mode:
                return [{"error": f"Collection '{coll}' not available. Use one of: {collection_enum}"}]
            r = by_mode.get(mode)
            if r is None:
                return [{"error": f"Search mode '{mode}' not available. Use one of: {search_mode_enum}"}]
            return r.retrieve(q, k=k)
    elif retrievers is not None and len(retrievers) > 0:
        search_mode_enum = sorted(retrievers.keys())
        default_mode = search_mode_enum[0] if "semantic" not in search_mode_enum else "semantic"

        def search_documents(**kwargs):
            q = kwargs.get("query", "")
            k = kwargs.get("k", default_k)
            mode = kwargs.get("search_mode", default_mode)
            r = retrievers.get(mode)
            if r is None:
                return [{"error": f"Search mode '{mode}' not available. Use one of: {search_mode_enum}"}]
            return r.retrieve(q, k=k)
    else:
        search_mode_enum = ["semantic"]
        default_mode = "semantic"

        def search_documents(**kwargs):
            q = kwargs.get("query", "")
            k = kwargs.get("k", default_k)
            return retriever.retrieve(q, k=k)

    search_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "k": {"type": "integer", "description": "Number of documents to return", "default": default_k},
            "search_mode": {
                "type": "string",
                "description": "Search mode: semantic (default), keyword (BM25), or hybrid.",
                "enum": search_mode_enum,
                "default": default_mode,
            },
        },
        "required": ["query"],
    }
    if multi_collection and collection_enum:
        search_schema["properties"]["collection_name"] = {
            "type": "string",
            "description": "Which collection to search. Use artemis_system_docs for system/docs/RAG/planning; use artemis_user_docs (or default) for user data and general tasks.",
            "enum": collection_enum,
            "default": default_coll,
        }
    registry.register(
        "search_documents",
        search_documents,
        description="Search the knowledge base for relevant documents. Returns a list of {text, score, metadata}. When multiple collections exist, pass collection_name: artemis_system_docs for system knowledge, artemis_user_docs for user data. Optional search_mode: semantic (default), keyword, hybrid.",
        parameters_schema=search_schema,
    )

    def get_rag_options(**kwargs):
        """Return available RAG options (search modes, chunk strategies, CSV schemas, and collections when multi-collection) for the agent to answer questions about capabilities."""
        try:
            from artemis.rag.ingestion.chunkers.registry import CHUNKERS
            from artemis.rag.ingestion.converters.csv_converter import CSV_CONVERTERS, DocumentSchema
            chunk_strategies = [s.value for s in CHUNKERS.keys()]
            csv_schemas = [s.value for s in CSV_CONVERTERS.keys()] if CSV_CONVERTERS else [s.value for s in DocumentSchema]
        except ImportError:
            chunk_strategies = []
            csv_schemas = []
        out = {
            "search_modes": search_mode_enum,
            "chunk_strategies": chunk_strategies,
            "csv_schemas": csv_schemas,
        }
        if multi_collection and collection_enum:
            out["collections"] = collection_enum
            out["collection_usage"] = "artemis_system_docs = system/docs/RAG/planning; artemis_user_docs = user data (default)"
        return out

    registry.register(
        "get_rag_options",
        get_rag_options,
        description="Return the list of available RAG options: search modes (for search_documents), chunk strategies and CSV schemas (for ingest). Use this when the user asks what search or chunking options are available.",
        parameters_schema={
            "type": "object",
            "properties": {},
        },
    )

    def suggest_ingest_options_kw(**kwargs):
        path = kwargs.get("path", "").strip()
        path_type = kwargs.get("path_type")
        if not path:
            return {"ok": False, "error": "path is required", "reasoning": "Provide a file or directory path."}
        return suggest_ingest_options(path, path_type=path_type)

    registry.register(
        "suggest_ingest_options",
        suggest_ingest_options_kw,
        description="Get recommended ingest options (file_type, chunk_strategy, chunk_size, overlap, file_extension for dirs, schema for CSV) for a given file or directory path. Call this BEFORE ingest_file or ingest_directory when the user asks to ingest a path, then use the returned options in the ingest call.",
        parameters_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path or directory path to analyze for ingest options."},
                "path_type": {
                    "type": "string",
                    "description": "Optional: 'file' or 'directory' to force type; omit to auto-detect from path.",
                    "enum": ["file", "directory"],
                },
            },
            "required": ["path"],
        },
    )

    if indexer is not None or (multi_collection and indexers):
        from artemis.rag.ingestion.chunkers.registry import CHUNKERS
        from artemis.rag.ingestion.converters.csv_converter import CSV_CONVERTERS, DocumentSchema

        chunk_strategy_enum = [s.value for s in CHUNKERS.keys()]
        schema_enum = [s.value for s in CSV_CONVERTERS.keys()] if CSV_CONVERTERS else [s.value for s in DocumentSchema]

        if multi_collection and indexers:
            def ingest_file_kw(**kwargs):
                coll = kwargs.get("collection_name") or default_coll
                idx = indexers.get(coll)
                if idx is None:
                    return [{"error": f"Collection '{coll}' not available. Use one of: {collection_enum}"}]
                ingest_fn = create_rag_ingest_tool(idx)
                k = dict(kwargs)
                if k.get("chunk_strategy") == "agentic" and llm_client_for_agentic is not None:
                    k["llm_client"] = llm_client_for_agentic
                return ingest_fn(
                    k.get("path", ""),
                    k.get("file_type", "text"),
                    chunk_strategy=k.get("chunk_strategy"),
                    chunk_size=k.get("chunk_size"),
                    overlap=k.get("overlap"),
                    schema=k.get("schema"),
                    llm_client=k.get("llm_client"),
                )

            ingest_file_schema = {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "file_type": {"type": "string", "enum": ["csv", "pdf", "docx", "md", "text"]},
                    "collection_name": {
                        "type": "string",
                        "description": "Which collection to ingest into. Use artemis_system_docs for system docs; artemis_user_docs for user data (default).",
                        "enum": collection_enum,
                        "default": default_coll,
                    },
                    "chunk_strategy": {
                        "type": "string",
                        "description": "Optional. One of: " + ", ".join(chunk_strategy_enum) + ". For CSV only csv_row or omit.",
                        "enum": chunk_strategy_enum,
                    },
                    "chunk_size": {"type": "integer", "description": "Optional. Chunk size for fixed/fixed_overlap."},
                    "overlap": {"type": "integer", "description": "Optional. Overlap for fixed_overlap."},
                    "schema": {
                        "type": "string",
                        "description": "Optional. CSV only: document schema.",
                        "enum": schema_enum,
                    },
                },
                "required": ["path", "file_type"],
            }
        else:
            ingest_fn = create_rag_ingest_tool(indexer)

            def ingest_file_kw(**kwargs):
                k = dict(kwargs)
                if k.get("chunk_strategy") == "agentic" and llm_client_for_agentic is not None:
                    k["llm_client"] = llm_client_for_agentic
                return ingest_fn(
                    k.get("path", ""),
                    k.get("file_type", "text"),
                    chunk_strategy=k.get("chunk_strategy"),
                    chunk_size=k.get("chunk_size"),
                    overlap=k.get("overlap"),
                    schema=k.get("schema"),
                    llm_client=k.get("llm_client"),
                )

            ingest_file_schema = {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "file_type": {"type": "string", "enum": ["csv", "pdf", "docx", "md", "text"]},
                    "chunk_strategy": {
                        "type": "string",
                        "description": "Optional. One of: " + ", ".join(chunk_strategy_enum) + ". For CSV only csv_row or omit.",
                        "enum": chunk_strategy_enum,
                    },
                    "chunk_size": {"type": "integer", "description": "Optional. Chunk size for fixed/fixed_overlap."},
                    "overlap": {"type": "integer", "description": "Optional. Overlap for fixed_overlap."},
                    "schema": {
                        "type": "string",
                        "description": "Optional. CSV only: document schema.",
                        "enum": schema_enum,
                    },
                },
                "required": ["path", "file_type"],
            }

        registry.register(
            "ingest_file",
            ingest_file_kw,
            description="Ingest a file into the knowledge base. file_type: csv, pdf, docx, md, text. When multiple collections exist, pass collection_name: artemis_system_docs for system docs, artemis_user_docs for user data. Optional: chunk_strategy, chunk_size, overlap; for CSV only: schema.",
            parameters_schema=ingest_file_schema,
        )

        if multi_collection and indexers:
            def ingest_directory_kw(**kwargs):
                coll = kwargs.get("collection_name") or default_coll
                idx = indexers.get(coll)
                if idx is None:
                    return [{"error": f"Collection '{coll}' not available. Use one of: {collection_enum}"}]
                ingest_dir_fn = create_rag_ingest_directory_tool(idx, default_extension="md")
                llm = llm_client_for_agentic if kwargs.get("chunk_strategy") == "agentic" else None
                return ingest_dir_fn(
                    kwargs.get("directory_path", ""),
                    kwargs.get("file_extension", "md"),
                    chunk_strategy=kwargs.get("chunk_strategy"),
                    chunk_size=kwargs.get("chunk_size"),
                    overlap=kwargs.get("overlap"),
                    llm_client=llm,
                )

            ingest_dir_schema = {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string"},
                    "file_extension": {"type": "string", "default": "md"},
                    "collection_name": {
                        "type": "string",
                        "description": "Which collection to ingest into. artemis_system_docs for system docs; artemis_user_docs for user data (default).",
                        "enum": collection_enum,
                        "default": default_coll,
                    },
                    "chunk_strategy": {
                        "type": "string",
                        "description": "Optional. One of: " + ", ".join(chunk_strategy_enum) + ".",
                        "enum": chunk_strategy_enum,
                    },
                    "chunk_size": {"type": "integer", "description": "Optional. Chunk size for fixed/fixed_overlap."},
                    "overlap": {"type": "integer", "description": "Optional. Overlap for fixed_overlap."},
                },
                "required": ["directory_path"],
            }
        else:
            ingest_dir_fn = create_rag_ingest_directory_tool(indexer, default_extension="md")

            def ingest_directory_kw(**kwargs):
                llm = llm_client_for_agentic if kwargs.get("chunk_strategy") == "agentic" else None
                return ingest_dir_fn(
                    kwargs.get("directory_path", ""),
                    kwargs.get("file_extension", "md"),
                    chunk_strategy=kwargs.get("chunk_strategy"),
                    chunk_size=kwargs.get("chunk_size"),
                    overlap=kwargs.get("overlap"),
                    llm_client=llm,
                )

            ingest_dir_schema = {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string"},
                    "file_extension": {"type": "string", "default": "md"},
                    "chunk_strategy": {
                        "type": "string",
                        "description": "Optional. One of: " + ", ".join(chunk_strategy_enum) + ".",
                        "enum": chunk_strategy_enum,
                    },
                    "chunk_size": {"type": "integer", "description": "Optional. Chunk size for fixed/fixed_overlap."},
                    "overlap": {"type": "integer", "description": "Optional. Overlap for fixed_overlap."},
                },
                "required": ["directory_path"],
            }

        registry.register(
            "ingest_directory",
            ingest_directory_kw,
            description="Ingest all files in a directory (e.g. RAG_demo/techcorp_docs). When multiple collections exist, pass collection_name. file_extension: md, pdf, txt, etc.; default md. Optional: chunk_strategy, chunk_size, overlap.",
            parameters_schema=ingest_dir_schema,
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
