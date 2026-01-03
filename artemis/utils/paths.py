"""
Path utilities for A.R.T.E.M.I.S.

Provides centralized paths for logs, generated documents, and other data files.
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Assumes this file is in artemis/utils/, so project root is 2 levels up.
    
    Returns:
        Path to project root directory
    """
    # This file is at artemis/utils/paths.py
    # Project root is 2 levels up
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """
    Get the centralized data directory for A.R.T.E.M.I.S.
    
    Creates artemis_data/ folder at project root with subfolders:
    - logs/ for log files
    - docs/ for generated documents
    
    Returns:
        Path to artemis_data/ directory
    """
    project_root = get_project_root()
    data_dir = project_root / "artemis_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_logs_dir() -> Path:
    """
    Get the logs directory.
    
    Returns:
        Path to artemis_data/logs/ directory
    """
    logs_dir = get_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_docs_dir() -> Path:
    """
    Get the generated documents directory.
    
    Returns:
        Path to artemis_data/docs/ directory
    """
    docs_dir = get_data_dir() / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir

