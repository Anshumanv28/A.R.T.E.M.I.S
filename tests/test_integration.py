import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from artemis.agent.config import AgentConfig
from artemis.agent.run import get_v2_runtime, run_agent_v2, _build_registry_v2
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.retriever import Retriever, RetrievalMode
from artemis.api import app

# Skip the entire module if credentials are missing
pytestmark = pytest.mark.skipif(
    not (os.getenv("QDRANT_URL") and (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"))),
    reason="Integration tests require QDRANT_URL and an LLM API key (GROQ_API_KEY or OPENAI_API_KEY)"
)

TEST_COLLECTION = "artemis_test"

@pytest.fixture(scope="module")
def live_config():
    """Load config from real environment variables."""
    return AgentConfig.from_env()

@pytest.fixture(scope="module")
def test_registry(live_config):
    """
    Sets up the 'artemis_test' collection.
    Clears it (if exists), ingests dummy data to create it, and returns a registry
    pointed entirely at this test collection.
    """
    indexer = Indexer(collection_name=TEST_COLLECTION)
    
    # Attempt to clear the collection to ensure a clean state
    try:
        indexer.qdrant_client.delete_collection(TEST_COLLECTION)
    except Exception:
        # Collection might not exist yet, ignore
        pass
        
    # Ingesting dummy data forces creation of the collection & embedding indices
    dummy_text = "This is a test document about Artemis integration testing."
    indexer.add_documents([dummy_text])
    
    # Build retriever and registry
    retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
    registry = _build_registry_v2(live_config, retriever, indexer, TEST_COLLECTION)
    
    yield registry
    
    # Optional teardown: clean up after all tests in module finish
    try:
        
        indexer.qdrant_client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass

@pytest.fixture(scope="module")
def test_client(live_config, test_registry):
    """Provide a synchronous TestClient for the FastAPI app."""
    # Override the app lifespan state
    app.state.config = live_config
    app.state.registry = test_registry
    app.state.ready = True
    
    with TestClient(app) as client:
        yield client

def test_get_v2_runtime_initializes():
    """Health / startup — get_v2_runtime() initialises without errors given valid env vars"""
    config, registry = get_v2_runtime()
    assert config is not None
    assert registry is not None

def test_supervisor_routing_rag_search(live_config, test_registry):
    """Supervisor routing — rag_search"""
    result = run_agent_v2(
        "What does the document say about Artemis integration testing?",
        config=live_config,
        registry=test_registry,
        collection_name=TEST_COLLECTION
    )
    
    assert result["routed_to"] == "rag_search"
    assert result.get("final_answer") is not None
    # Given the dummy data, the agent should ideally respond correctly
    answer = result["final_answer"].lower()
    assert "test" in answer or "artemis" in answer or "integration" in answer

def test_supervisor_routing_ingestion(live_config, test_registry, tmp_path):
    """Supervisor routing — ingestion"""
    # Create a small text file
    test_file = tmp_path / "test_ingest.txt"
    test_file.write_text("This is another test document for ingestion.")
    
    result = run_agent_v2(
        f"Please ingest the file {test_file}",
        config=live_config,
        registry=test_registry,
        collection_name=TEST_COLLECTION
    )
    
    assert result["routed_to"] == "ingestion"
    # Verify a tool was called (it might succeed or fail depending on if the agent
    # processes the path properly, but the router MUST invoke the ingestion agent/tools)
    tool_calls = result.get("tool_calls", [])
    assert len(tool_calls) > 0

def test_supervisor_routing_collection_management(live_config, test_registry):
    """Supervisor routing — collection_management"""
    result = run_agent_v2(
        "List all my Qdrant collections",
        config=live_config,
        registry=test_registry,
        collection_name=TEST_COLLECTION
    )
    
    assert result["routed_to"] == "collection_management"
    tool_calls = result.get("tool_calls", [])
    assert len(tool_calls) > 0
    # Expected tool for listing
    assert any(call.get("name") == "list_collections" for call in tool_calls)

def test_supervisor_routing_direct(live_config, test_registry):
    """Supervisor routing — direct"""
    result = run_agent_v2(
        "Thanks",
        config=live_config,
        registry=test_registry,
        collection_name=TEST_COLLECTION
    )
    
    assert result["routed_to"] == "direct"
    assert len(result.get("tool_calls", [])) == 0

def test_api_health(test_client):
    """API /health — GET /health returns 200 and {'status': 'ok'} when Qdrant is reachable"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_api_query(test_client):
    """API /query — POST /query with a real query returns {final_answer, routed_to} with no error"""
    payload = {"query": "Hello"}
    response = test_client.post("/query", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "final_answer" in data
    assert data["routed_to"] == "direct"
    assert data.get("error") is None

def test_multi_turn(test_client):
    """Multi-turn — two consecutive queries share message_history correctly"""
    # Turn 1
    payload1 = {"query": "My name is IntegrationTester"}
    response1 = test_client.post("/query", json=payload1)
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Build history
    history = [
        {"role": "user", "content": payload1["query"]},
        {"role": "assistant", "content": data1["final_answer"]}
    ]
    
    # Turn 2
    payload2 = {"query": "What is my name?", "message_history": history}
    response2 = test_client.post("/query", json=payload2)
    assert response2.status_code == 200
    data2 = response2.json()
    
    assert "IntegrationTester" in data2["final_answer"]
    assert data2["routed_to"] == "direct"
