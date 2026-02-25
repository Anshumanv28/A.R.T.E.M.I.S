# Agent Layer Quick Start Guide

The A.R.T.E.M.I.S agent layer provides a LangGraph-based orchestration system that intelligently routes queries between RAG (Retrieval-Augmented Generation) and direct answer paths.

## Overview

The agent layer consists of:
- **Planner Node**: Classifies query intent (RAG vs direct)
- **RAG Node**: Retrieves documents and synthesizes answers with citations
- **Direct Answer Node**: Answers queries without document retrieval
- **Graph Orchestration**: Routes between nodes based on intent

## Prerequisites

1. **Environment Variables**: Set up your `.env` file with required API keys:
   ```bash
   # Required for Groq (default provider)
   GROQ_API_KEY=your-groq-api-key
   
   # Optional for OpenAI
   OPENAI_API_KEY=your-openai-api-key
   
   # Required for RAG functionality
   QDRANT_URL=your-qdrant-url
   QDRANT_API_KEY=your-qdrant-api-key
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install -e .
   ```

3. **Indexed Documents**: Ensure you have documents indexed in Qdrant (see [PDF RAG Example](../examples/README_PDF_RAG.md))

## Quick Start

### Basic Usage

```python
from artemis.agent import run_agent
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.retriever import Retriever, RetrievalMode

# Step 1: Create indexer and retriever (if you haven't already)
indexer = Indexer(collection_name="my_documents")
# ... index your documents ...

retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)

# Step 2: Run agent with a query
result = run_agent(
    query="What is the main topic of the documents?",
    retriever=retriever
)

# Step 3: Access the answer
print(result["final_answer"])
print(f"Intent: {result['intent']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Retrieved {len(result['retrieved_docs'])} documents")
```

### Using Custom Configuration

```python
from artemis.agent import AgentConfig, AgentGraph
from artemis.rag.core.retriever import Retriever, RetrievalMode

# Create custom config
config = AgentConfig(
    provider="groq",  # or "openai"
    model_name="llama-3.3-70b-versatile",
    max_tokens=2048,
    temperature=0.7,
    retrieval_k=5
)

# Create retriever
retriever = Retriever(mode=RetrievalMode.SEMANTIC, collection_name="my_documents")

# Create agent graph
agent = AgentGraph(config=config, retriever=retriever)

# Run query
result = agent.invoke("What are the key points?")

print(result["final_answer"])
```

### Command Line Interface

Run the agent interactively:

```bash
python -m artemis.agent.run
```

Or with a single query:

```bash
python -m artemis.agent.run "What is the main topic?"
```

With custom options:

```bash
python -m artemis.agent.run \
    --collection my_documents \
    --provider groq \
    --model llama-3.3-70b-versatile \
    "Your query here"
```

## How It Works

### Flow Diagram

```
Start → Planner → [Intent Classification]
                    ↓
            ┌───────┴───────┐
            │               │
        intent=rag    intent=direct
            │               │
            ↓               ↓
        RAG Node    Direct Answer Node
            │               │
            └───────┬───────┘
                    ↓
                   END
```

### Intent Classification

The planner node uses an LLM to classify queries:

- **RAG Path**: Used when query asks about:
  - Specific documents or indexed content
  - Information that might be in the knowledge base
  - Document-specific questions ("what does X say about Y")

- **Direct Path**: Used when query:
  - Is a general question not referencing documents
  - Asks for concept explanations
  - Is conversational without needing retrieval

### RAG Node Process

1. **Retrieve**: Calls `Retriever.retrieve()` to get top-k documents
2. **Format**: Formats documents with scores and metadata
3. **Synthesize**: Uses LLM to generate answer with citations [1], [2], etc.
4. **Return**: Stores both `retrieved_docs` and `final_answer` in state

## Configuration Options

### Environment Variables

You can configure the agent via environment variables:

```bash
# LLM Provider (groq or openai)
ARTEMIS_LLM_PROVIDER=groq

# Model name
ARTEMIS_LLM_MODEL=llama-3.3-70b-versatile

# Generation parameters
ARTEMIS_MAX_TOKENS=2048
ARTEMIS_TEMPERATURE=0.7

# Retrieval parameters
ARTEMIS_RETRIEVAL_K=5
```

### Programmatic Configuration

```python
from artemis.agent import AgentConfig

# From environment with overrides
config = AgentConfig.from_env(
    provider="openai",
    model_name="gpt-4o-mini",
    temperature=0.5
)

# Direct instantiation
config = AgentConfig(
    provider="groq",
    model_name="llama-3.3-70b-versatile",
    max_tokens=2048,
    temperature=0.7,
    retrieval_k=5,
    groq_api_key="your-key"  # Optional if in env
)
```

## State Structure

The agent state contains:

```python
{
    "query": str,                    # Input query
    "intent": "rag" | "direct",      # Classified intent
    "confidence": float,             # Confidence score (0.0-1.0)
    "retrieved_docs": List[Dict],    # Retrieved documents (RAG path)
    "tool_calls": List[Dict],        # Tool calls (future)
    "final_answer": str,             # Generated answer
    "error": Optional[str]           # Error message if any
}
```

## Examples

### Example 1: Document Query (RAG Path)

```python
result = run_agent(
    query="What does the HR policy say about vacation days?",
    retriever=retriever
)

# Result will use RAG path
print(result["intent"])  # "rag"
print(result["final_answer"])  # Answer with citations
print(len(result["retrieved_docs"]))  # Number of retrieved docs
```

### Example 2: General Question (Direct Path)

```python
result = run_agent(
    query="What is machine learning?",
    retriever=retriever
)

# Result will use direct path
print(result["intent"])  # "direct"
print(result["final_answer"])  # Direct answer
print(len(result["retrieved_docs"]))  # 0
```

## Error Handling

The agent handles errors gracefully:

- **Retrieval Errors**: Falls back to direct answer or error message
- **LLM Errors**: Returns error in state with partial results
- **Configuration Errors**: Raises ValueError with helpful messages

Check for errors:

```python
result = run_agent(query="...", retriever=retriever)

if result.get("error"):
    print(f"Error: {result['error']}")
else:
    print(result["final_answer"])
```

## Advanced Usage

### Custom Retriever

```python
from artemis.rag.core.retriever import Retriever, RetrievalMode
from artemis.rag.core.indexer import Indexer

# Create indexer with custom settings
indexer = Indexer(
    collection_name="custom_collection",
    embedder=Embedder(model_name="custom-model")
)

# Create retriever
retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    indexer=indexer
)

# Use with agent
result = run_agent(query="...", retriever=retriever)
```

### Async Usage

```python
import asyncio
from artemis.agent import AgentConfig, AgentGraph

async def main():
    config = AgentConfig.from_env()
    retriever = Retriever(...)
    agent = AgentGraph(config=config, retriever=retriever)
    
    result = await agent.ainvoke("Your query")
    print(result["final_answer"])

asyncio.run(main())
```

## Troubleshooting

### "GROQ_API_KEY not found"
- Set `GROQ_API_KEY` in your `.env` file
- Or pass `groq_api_key` parameter to `AgentConfig`

### "Collection does not exist"
- Ensure documents are indexed in Qdrant
- Check collection name matches your indexer

### "No documents retrieved"
- Verify documents are indexed
- Check query relevance
- Try increasing `retrieval_k` in config

### Low Confidence Scores
- Normal for ambiguous queries
- Agent defaults to RAG path on low confidence
- Adjust planner prompts if needed

## Next Steps

- Explore the [PDF RAG Example](../examples/README_PDF_RAG.md) for document indexing
- Check [Architecture Flow](../ARCHITECTURE_FLOW.md) for system overview
- See [Main README](../README.md) for project details

## Notes

- The agent layer is a thin orchestration wrapper around existing RAG components
- All RAG internals remain unchanged
- Tool execution and multi-step reasoning are planned for future phases
- Current implementation focuses on single-turn Q&A with optional RAG
