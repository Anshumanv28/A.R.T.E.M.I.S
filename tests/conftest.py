"""
Pytest fixtures and utilities for A.R.T.E.M.I.S. tests.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest


# --- Agent fixtures (for test_agent_*.py) ---


class MockRetriever:
    """Mock retriever for agent tests; no Qdrant required."""

    def __init__(self, docs: List[Dict[str, Any]] = None):
        self.docs = docs or [{"text": "Test doc.", "score": 0.9, "metadata": {}}]
        self.retrieve_calls = []

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        self.retrieve_calls.append((query, k))
        return self.docs[:k]


@pytest.fixture
def mock_retriever():
    """Retriever mock with retrieve(query, k=5) returning a fixed list of doc dicts."""
    return MockRetriever()


@pytest.fixture
def agent_config():
    """AgentConfig with test API key so tests don't depend on env."""
    from artemis.agent.config import AgentConfig
    return AgentConfig(
        provider="groq",
        groq_api_key="test-key",
        max_tool_steps=10,
    )


def create_temp_csv(content: str = None) -> Path:
    """
    Create a temporary CSV file for testing.
    
    Args:
        content: Optional CSV content. If None, creates a simple test CSV.
        
    Returns:
        Path to temporary CSV file
    """
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    if content is None:
        # Default test CSV
        content = "name,value,rating\nTest1,100,4.5\nTest2,200,4.8\nTest3,300,4.2"
    
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


def create_temp_text(content: str = "This is a test document.") -> Path:
    """Create a temporary text file for testing."""
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


def create_temp_markdown(content: str = "# Test Document\n\nThis is test content.") -> Path:
    """Create a temporary Markdown file for testing."""
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


# Sample CSV data for testing
SAMPLE_RESTAURANT_CSV = """restaurant_id,restaurant_name,city,cuisines,rating,price_for_two
1,Le Petit Souffle,Makati City,French Japanese,4.8,1500
2,Spice Garden,Mumbai,Indian North Indian,4.5,800
3,Pasta Paradise,Delhi,Italian,4.7,1200"""

SAMPLE_TRAVEL_CSV = """hotel_name,city,country,price_per_night,rating,amenities
Grand Hotel,Paris,France,200,4.5,WiFi Pool Spa
Beach Resort,Bali,Indonesia,150,4.8,Beachfront WiFi
City Hotel,Tokyo,Japan,250,4.7,WiFi Restaurant"""

SAMPLE_TEXT_CONTENT = """This is a test document with multiple paragraphs.

It contains several sentences that can be used for testing chunking strategies.

The document should be processed correctly by the loaders and chunkers."""

SAMPLE_MARKDOWN_CONTENT = """# Test Document

This is a test markdown document.

## Section 1

Content for section 1.

### Subsection 1.1

More content here.

## Section 2

Content for section 2.
"""

