"""
RAG tools for agent use.

Thin callable wrappers around Retriever, Indexer/ingest_file, and collection_manager
so the agent can search, ingest, and manage collections via a tool-calling node.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from artemis.utils import get_logger

logger = get_logger(__name__)

# Optional imports so tools can be used when deps are available
try:
    from artemis.rag.core import Retriever, Indexer
    from artemis.rag.core.collection_manager import (
        list_collections,
        get_collection_info,
        create_collection,
        clear_collection,
        delete_collection,
    )
    from artemis.rag.ingestion import (
        ingest_file,
        FileType,
        ChunkStrategy,
        DocumentSchema,
    )
    _TOOLS_AVAILABLE = True
except ImportError:
    Retriever = None
    Indexer = None
    list_collections = None
    get_collection_info = None
    create_collection = None
    clear_collection = None
    delete_collection = None
    ingest_file = None
    FileType = None
    ChunkStrategy = None
    DocumentSchema = None
    _TOOLS_AVAILABLE = False


def create_rag_search_tool(
    retriever: "Retriever",
    k: int = 5,
) -> Callable[[str], List[Dict[str, Any]]]:
    """
    Create a search tool that queries the knowledge base.

    Returns a callable (query: str) -> list[dict] with keys text, score, metadata.
    Use this as the RAG search tool when registering tools for the agent.
    """
    def search(query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant documents."""
        return retriever.retrieve(query, k=k)

    return search


def create_rag_ingest_tool(
    indexer: "Indexer",
) -> Callable[[str, str], Dict[str, Any]]:
    """
    Create an ingest tool that adds a file to the RAG collection.

    Returns a callable (path: str, file_type: str) -> dict.
    file_type must be one of: csv, pdf, docx, md, text.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    _FILE_TYPE_MAP = {
        "csv": FileType.CSV,
        "pdf": FileType.PDF,
        "docx": FileType.DOCX,
        "md": FileType.MD,
        "text": FileType.TEXT,
    }

    def ingest(
        path: str,
        file_type: str,
        chunk_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        schema: Optional[str] = None,
        llm_client: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Ingest a file into the knowledge base. Pass llm_client for agentic chunking."""
        raw_path = (path or "").strip()
        if raw_path in ("", "."):
            return {
                "ok": False,
                "error": "path cannot be '.' or empty. Specify the file path (e.g. 'README.md').",
                "path": path,
            }
        path_obj = _resolve_path(path)
        if not path_obj.exists():
            return {"ok": False, "error": f"File not found: {path}"}
        ft_lower = file_type.strip().lower()
        if ft_lower not in _FILE_TYPE_MAP:
            return {
                "ok": False,
                "error": f"Unsupported file_type '{file_type}'. Use one of: csv, pdf, docx, md, text",
            }
        ft_enum = _FILE_TYPE_MAP[ft_lower]
        # CSV: only allow chunk_strategy csv_row or omit
        if ft_lower == "csv" and chunk_strategy is not None:
            cs_lower = chunk_strategy.strip().lower()
            if cs_lower != "csv_row":
                return {
                    "ok": False,
                    "error": f"For CSV files only chunk_strategy 'csv_row' or omit is allowed; got '{chunk_strategy}'",
                    "path": path,
                }
        strategy_enum = None
        if chunk_strategy is not None:
            cs_lower = chunk_strategy.strip().lower()
            try:
                strategy_enum = ChunkStrategy(cs_lower)
            except ValueError:
                return {
                    "ok": False,
                    "error": f"Unknown chunk_strategy '{chunk_strategy}'. Use one of: semantic, fixed, fixed_overlap, agentic, csv_row (CSV only).",
                    "path": path,
                }
        schema_enum = None
        if schema is not None:
            if ft_lower != "csv":
                return {
                    "ok": False,
                    "error": "schema is only valid when file_type is csv.",
                    "path": path,
                }
            try:
                schema_enum = DocumentSchema(schema.strip().lower())
            except ValueError:
                return {
                    "ok": False,
                    "error": f"Unknown schema '{schema}'. Use one of: restaurant, travel, support.",
                    "path": path,
                }
        chunk_kwargs: Dict[str, Any] = {}
        if chunk_size is not None:
            chunk_kwargs["chunk_size"] = chunk_size
        if overlap is not None:
            chunk_kwargs["overlap"] = overlap
        if llm_client is not None:
            chunk_kwargs["llm_client"] = llm_client
        try:
            ingest_file(
                path_obj,
                ft_enum,
                indexer,
                chunk_strategy=strategy_enum,
                schema=schema_enum,
                **chunk_kwargs,
            )
            collection = getattr(indexer, "collection_name", None)
            return {"ok": True, "path": path, "file_type": ft_lower, "collection": collection}
        except Exception as e:
            logger.exception(f"Ingest failed for {path}: {e}")
            return {"ok": False, "error": str(e), "path": path}

    return ingest


def create_rag_ingest_directory_tool(
    indexer: "Indexer",
    default_extension: str = "md",
) -> Callable[[str, str], Dict[str, Any]]:
    """
    Create a tool that ingests all files in a directory with a given extension.

    Returns a callable (directory_path: str, file_extension: str) -> dict with
    ok, ingested_count, failed_count, errors (list of str).
    file_extension defaults to "md" (markdown). Use "pdf", "txt", etc. for other types.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    _FILE_TYPE_MAP = {
        "csv": FileType.CSV,
        "pdf": FileType.PDF,
        "docx": FileType.DOCX,
        "md": FileType.MD,
        "text": FileType.TEXT,
        "txt": FileType.TEXT,
    }

    def ingest_directory(
        directory_path: str,
        file_extension: str = default_extension,
        chunk_strategy: Optional[str] = None,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        llm_client: Optional[Any] = None,
        recursive: bool = False,
    ) -> Dict[str, Any]:
        """Ingest files in the directory with the given extension. By default only files directly in the directory are ingested (no subdirectories). Set recursive=True to include subdirectories. Pass llm_client for agentic chunking."""
        raw = (directory_path or "").strip()
        if raw in ("", "."):
            return {
                "ok": False,
                "error": "directory_path cannot be '.' or empty. Specify the folder name the user asked for (e.g. 'docs' for the docs folder).",
                "ingested_count": 0,
            }
        dir_path = _resolve_path(directory_path)
        if not dir_path.exists():
            return {"ok": False, "error": f"Directory not found: {directory_path}", "ingested_count": 0}
        if not dir_path.is_dir():
            return {"ok": False, "error": f"Not a directory: {directory_path}", "ingested_count": 0}
        ext = file_extension.strip().lower().lstrip(".")
        if ext == "txt":
            pattern = "*.txt"
            file_type_key = "text"
        else:
            pattern = f"*.{ext}" if ext else "*.md"
            file_type_key = ext if ext in _FILE_TYPE_MAP else "md"
        ft = _FILE_TYPE_MAP.get(file_type_key, FileType.MD)
        strategy_enum = None
        if chunk_strategy is not None:
            try:
                strategy_enum = ChunkStrategy(chunk_strategy.strip().lower())
            except ValueError:
                return {
                    "ok": False,
                    "error": f"Unknown chunk_strategy '{chunk_strategy}'. Use one of: semantic, fixed, fixed_overlap, agentic.",
                    "ingested_count": 0,
                }
        chunk_kwargs: Dict[str, Any] = {}
        if chunk_size is not None:
            chunk_kwargs["chunk_size"] = chunk_size
        if overlap is not None:
            chunk_kwargs["overlap"] = overlap
        if llm_client is not None:
            chunk_kwargs["llm_client"] = llm_client
        files = list(dir_path.rglob(pattern) if recursive else dir_path.glob(pattern))
        # Skip files inside cache/hidden/version-control directories (e.g. .pytest_cache, __pycache__, .git)
        _skip_dirs = {".pytest_cache", "__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}
        def _should_skip(file_path: Path) -> bool:
            try:
                rel = file_path.relative_to(dir_path)
                for part in rel.parts[:-1]:  # parent dirs only
                    if part in _skip_dirs or (part.startswith(".") and part not in (".github",)):
                        return True
            except ValueError:
                pass
            return False
        ingested = 0
        errors = []
        for f in files:
            if not f.is_file() or _should_skip(f):
                continue
            try:
                ingest_file(
                    f,
                    ft,
                    indexer,
                    chunk_strategy=strategy_enum,
                    **chunk_kwargs,
                )
                ingested += 1
            except Exception as e:
                errors.append(f"{f.name}: {e}")
                logger.warning(f"Ingest failed for {f}: {e}")
        collection = getattr(indexer, "collection_name", None)
        return {
            "ok": len(errors) == 0 or ingested > 0,
            "ingested_count": ingested,
            "failed_count": len(errors),
            "errors": errors[:10],
            "collection": collection,
        }
    return ingest_directory


# Extension -> file_type string for ingest tool
_EXT_TO_FILETYPE = {
    ".csv": "csv",
    ".pdf": "pdf",
    ".docx": "docx",
    ".md": "md",
    ".markdown": "md",
    ".txt": "text",
}
_SUPPORTED_EXTENSIONS = set(_EXT_TO_FILETYPE.keys())

# Directories to skip when listing (cache, venv, version control)
_LIST_SKIP_DIRS = {".pytest_cache", "__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}


def list_directory(
    path: str = ".",
    max_depth: int = 1,
) -> Dict[str, Any]:
    """
    List directories and files at a given path. Use this to discover folder structure
    so the user (or agent) can choose what to ingest or explore.

    Args:
        path: Directory path to list; use "." or "" for current working directory.
        max_depth: How many levels to show (1 = only immediate children; 2 = children + grandchildren).

    Returns:
        dict with ok, path, resolved_path, directories (list of names), files (list of names),
        and optionally subdirs (when max_depth > 1) with same shape. Hidden/cache dirs are skipped.
    """
    raw = (path or ".").strip() or "."
    p = _resolve_path(raw)
    if not p.exists():
        return {
            "ok": False,
            "error": f"Path not found: {path}",
            "path": path,
        }
    if not p.is_dir():
        return {
            "ok": False,
            "error": f"Not a directory: {path}",
            "path": path,
        }

    def _should_skip(name: str) -> bool:
        if name in _LIST_SKIP_DIRS:
            return True
        if name.startswith(".") and name != ".github":
            return True
        return False

    def _one_level(d: Path) -> Dict[str, Any]:
        dirs: List[str] = []
        files_list: List[str] = []
        try:
            for item in sorted(d.iterdir()):
                if _should_skip(item.name):
                    continue
                if item.is_dir():
                    dirs.append(item.name)
                else:
                    files_list.append(item.name)
        except OSError as e:
            return {"directories": [], "files": [], "error": str(e)}
        return {"directories": dirs, "files": files_list}

    out: Dict[str, Any] = {
        "ok": True,
        "path": path,
        "resolved_path": str(p.resolve()),
        "max_depth": max_depth,
    }
    level = _one_level(p)
    out["directories"] = level.get("directories", [])
    out["files"] = level.get("files", [])

    if max_depth > 1:
        subdirs_info: List[Dict[str, Any]] = []
        for subname in out["directories"]:
            subpath = p / subname
            if not subpath.is_dir() or _should_skip(subname):
                continue
            sub_level = _one_level(subpath)
            subdirs_info.append({
                "name": subname,
                "directories": sub_level.get("directories", []),
                "files": sub_level.get("files", []),
            })
        out["subdirs"] = subdirs_info

    return out


def _resolve_path(path: str) -> Path:
    """Resolve path for filesystem use. If path has leading slashes and does not exist, try relative to cwd (e.g. /docs -> docs on Windows)."""
    path = path.strip()
    p = Path(path)
    if p.exists():
        return p
    if path.startswith(("/", "\\")):
        alt = path.lstrip("/\\")
        if alt and Path(alt).exists():
            return Path(alt)
    return p


def suggest_ingest_options(
    path: str,
    path_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Suggest ingest options (file_type, chunk_strategy, chunk_size, overlap, schema for CSV)
    based on the given file or directory path. Use this before calling ingest_file or
    ingest_directory so the agent can pass optimal options.

    Args:
        path: File path or directory path.
        path_type: "file", "directory", or None to auto-detect (path exists as file vs dir).

    Returns:
        dict with recommended options and reasoning, e.g.:
        - For file: file_type, chunk_strategy, chunk_size, overlap, schema (if CSV), reasoning.
        - For directory: directory_path, file_extension, chunk_strategy, chunk_size, overlap,
          file_count_by_ext (summary), reasoning.
    """
    p = _resolve_path(path)
    if not p.exists():
        return {
            "ok": False,
            "error": f"Path not found: {path}",
            "reasoning": "Path does not exist; check the path and try again.",
        }
    is_dir = p.is_dir()
    if path_type is not None:
        if path_type.strip().lower() == "directory":
            is_dir = True
        elif path_type.strip().lower() == "file":
            is_dir = False
    try:
        from artemis.rag.ingestion.chunkers.registry import (
            DEFAULT_CHUNK_FOR_FILETYPE,
            FileType,
            ChunkStrategy,
        )
    except ImportError:
        return {
            "ok": False,
            "error": "RAG ingestion module not available",
            "reasoning": "Cannot suggest options without chunker registry.",
        }
    # Sensible defaults by strategy
    chunk_size = 512
    overlap = 64
    reasoning_parts: List[str] = []

    if is_dir:
        files = [f for f in p.rglob("*") if f.is_file()]
        ext_counts: Dict[str, int] = {}
        for f in files:
            ext = f.suffix.lower()
            if ext in _EXT_TO_FILETYPE:
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if not ext_counts:
            return {
                "ok": False,
                "error": f"No supported files in directory: {path}",
                "supported_extensions": list(_EXT_TO_FILETYPE.keys()),
                "reasoning": "Directory has no files with extensions: csv, pdf, docx, md, txt.",
            }
        # Recommend dominant extension (prefer md/pdf for docs, then csv, then others)
        order = (".md", ".pdf", ".txt", ".docx", ".csv")
        dominant_ext = max(ext_counts.keys(), key=lambda e: (ext_counts[e], -(order.index(e) if e in order else 99)))
        file_type_key = _EXT_TO_FILETYPE.get(dominant_ext, "md")
        ft_enum = getattr(FileType, file_type_key.upper(), FileType.MD)
        strategy = DEFAULT_CHUNK_FOR_FILETYPE.get(ft_enum, ChunkStrategy.FIXED_OVERLAP)
        file_extension = dominant_ext.lstrip(".")
        if file_extension == "text":
            file_extension = "txt"
        reasoning_parts.append(f"Directory has {sum(ext_counts.values())} supported file(s); dominant type: {file_extension} ({ext_counts.get(dominant_ext, 0)} files).")
        reasoning_parts.append(f"Recommended chunk_strategy '{strategy.value}' and file_extension '{file_extension}' for this content type.")
        out = {
            "ok": True,
            "path_type": "directory",
            "directory_path": path,
            "file_extension": file_extension,
            "chunk_strategy": strategy.value,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "file_count_by_extension": ext_counts,
            "reasoning": " ".join(reasoning_parts),
        }
        if file_type_key == "csv":
            out["schema"] = "optional: one of restaurant, travel, support (use if CSV has matching structure)"
        return out

    # Single file
    ext = p.suffix.lower()
    if ext not in _EXT_TO_FILETYPE:
        return {
            "ok": False,
            "error": f"Unsupported file extension: {ext}",
            "path": path,
            "supported_extensions": list(_EXT_TO_FILETYPE.keys()),
            "reasoning": "Use a supported type: csv, pdf, docx, md, txt.",
        }
    file_type = _EXT_TO_FILETYPE[ext]
    ft_enum = getattr(FileType, file_type.upper(), FileType.TEXT)
    strategy = DEFAULT_CHUNK_FOR_FILETYPE.get(ft_enum, ChunkStrategy.FIXED_OVERLAP)
    reasoning_parts.append(f"File type '{file_type}' detected; recommended chunk_strategy '{strategy.value}' for best results.")
    out = {
        "ok": True,
        "path_type": "file",
        "path": path,
        "file_type": file_type,
        "chunk_strategy": strategy.value,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "reasoning": " ".join(reasoning_parts),
    }
    if file_type == "csv":
        try:
            import csv as csv_module
            with open(p, newline="", encoding="utf-8", errors="replace") as f:
                reader = csv_module.reader(f)
                headers = next(reader, [])
            headers_lower = [h.strip().lower() for h in headers if isinstance(h, str)]
            if headers_lower:
                if any(k in " ".join(headers_lower) for k in ("name", "cuisine", "menu", "restaurant", "rating")):
                    out["schema"] = "restaurant"
                    out["reasoning"] += " CSV columns suggest schema 'restaurant'."
                elif any(k in " ".join(headers_lower) for k in ("flight", "hotel", "destination", "travel", "booking")):
                    out["schema"] = "travel"
                    out["reasoning"] += " CSV columns suggest schema 'travel'."
                elif any(k in " ".join(headers_lower) for k in ("ticket", "support", "customer", "issue", "status")):
                    out["schema"] = "support"
                    out["reasoning"] += " CSV columns suggest schema 'support'."
                else:
                    out["schema"] = "optional: restaurant, travel, or support if structure matches"
        except Exception:
            out["schema"] = "optional: restaurant, travel, or support if structure matches"
    return out


def list_collections_tool() -> List[str]:
    """
    List all Qdrant collection names.

    Uses QDRANT_URL and QDRANT_API_KEY from environment.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return list_collections()


def get_collection_info_tool(collection_name: str) -> Dict[str, Any]:
    """
    Get information about a collection (points count, status, etc.).

    Uses Qdrant env vars.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return get_collection_info(collection_name)


def create_collection_tool(
    collection_name: str,
    embedding_dim: Optional[int] = None,
) -> bool:
    """
    Create a new Qdrant collection.

    Uses Qdrant env vars. embedding_dim defaults to embedder dimension if not set.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return create_collection(
        collection_name=collection_name,
        embedding_dim=embedding_dim,
    )


def clear_collection_tool(
    collection_name: str,
    confirm: bool = False,
) -> bool:
    """
    Clear all points from a collection (keeps the collection).

    Requires confirm=True. Only set confirm after user has approved.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return clear_collection(
        collection_name=collection_name,
        confirm=confirm,
    )


def delete_collection_tool(
    collection_name: str,
    confirm: bool = False,
) -> bool:
    """
    Delete a collection entirely.

    Requires confirm=True. Only set confirm after user has approved.
    """
    if not _TOOLS_AVAILABLE:
        raise RuntimeError("RAG tools require qdrant-client and artemis.rag dependencies.")
    return delete_collection(
        collection_name=collection_name,
        confirm=confirm,
    )


__all__ = [
    "create_rag_search_tool",
    "create_rag_ingest_tool",
    "create_rag_ingest_directory_tool",
    "suggest_ingest_options",
    "list_directory",
    "list_collections_tool",
    "get_collection_info_tool",
    "create_collection_tool",
    "clear_collection_tool",
    "delete_collection_tool",
]
