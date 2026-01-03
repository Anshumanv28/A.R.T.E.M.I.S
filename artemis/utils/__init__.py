"""
Utility modules for A.R.T.E.M.I.S.
"""

from artemis.utils.logger import get_logger, setup_logger
from artemis.utils.paths import get_project_root, get_data_dir, get_logs_dir, get_docs_dir

__all__ = [
    "get_logger",
    "setup_logger",
    "get_project_root",
    "get_data_dir",
    "get_logs_dir",
    "get_docs_dir",
]

