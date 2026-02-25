# Testing the LangGraph Agent

This guide walks you through testing the A.R.T.E.M.I.S LangGraph agent layer.

## Prerequisites

Before testing, ensure you have:

1. **Environment Variables Set** (in `.env` or exported):

   ```bash
   # Required
   QDRANT_URL=your-qdrant-url
   QDRANT_API_KEY=your-qdrant-api-key
   GROQ_API_KEY=your-groq-api-key

   # Optional (for OpenAI)
   OPENAI_API_KEY=your-openai-api-key
   ```

2. **Documents Indexed in Qdrant**:
   - You need at least one collection with indexed documents
   - If you don't have documents yet, see [Quick Setup](#quick-setup-with-sample-data) below

3. **Dependencies Installed**:
   ```bash
   pip install -e .
   ```

## Quick Setup with Sample Data

If you don't have documents indexed yet, you can quickly set up test data:

### Option 1: Use PDF RAG Example

```bash
# This will index HR-Policy.pdf (if it exists) or prompt for a PDF
python examples/pdf_rag_example.py
```

This creates a collection called `pdf_documents` with your PDF content.

### Option 2: Use Existing Collection

If you already have documents indexed (from previous tests), you can use that collection name.

## Testing Methods

### Method 1: Quick CLI Test (Fastest)

Test the agent with a single query:

```bash
# Single query
python -m artemis.agent.run "What is machine learning?"

# With custom collection
python -m artemis.agent.run --collection my_documents "What does the document say about X?"

# Interactive mode
python -m artemis.agent.run
```

**Expected Output:**

- Answer text
- Intent classification (`rag` or `direct`)
- Confidence score
- Number of retrieved documents (if RAG path)

### Method 2: Full Demo Script (Recommended)

Run the comprehensive demo that tests multiple scenarios:

```bash
python examples/agent_demo.py
```

**What it does:**

1. ✅ Checks environment variables
2. ✅ Validates Qdrant connection
3. ✅ Tests example queries (RAG vs direct routing)
4. ✅ Enters interactive mode for custom queries

**Expected Flow:**

```
🤖🤖🤖... A.R.T.E.M.I.S Agent Demo
======================================================================
STEP 1: Environment Check
======================================================================
🔍 Checking environment variables...
   ✅ QDRANT_URL is set
   ✅ QDRANT_API_KEY is set
   ✅ GROQ_API_KEY is set

======================================================================
STEP 2: Setup Indexer
======================================================================
   Enter collection name (or press Enter for 'artemis_documents'):

======================================================================
STEP 3: Test Queries
======================================================================
Query 1: What is machine learning?
Expected: direct path (General question)
✅ Answer: Machine learning is...
📊 Agent State:
   Intent: direct
   Confidence: 0.85
   Retrieved Docs: 0

Query 2: What does the document say about vacation policies?
Expected: rag path (Document-specific question)
✅ Answer: According to the document [1]...
📊 Agent State:
   Intent: rag
   Confidence: 0.92
   Retrieved Docs: 5
```

### Method 3: Python Programmatic Test

Test the agent programmatically in your own script:

```python
from artemis.agent import run_agent
from artemis.rag.core.indexer import Indexer

# Create indexer (assumes collection already exists with documents)
indexer = Indexer(collection_name="your_collection_name")

# Test RAG query
result = run_agent(
    query="What does the document say about X?",
    indexer=indexer
)

print(f"Answer: {result['final_answer']}")
print(f"Intent: {result['intent']}")
print(f"Confidence: {result['confidence']:.2f}")
print(f"Retrieved {len(result['retrieved_docs'])} documents")

# Test direct query
result2 = run_agent(
    query="What is artificial intelligence?",
    indexer=indexer
)

print(f"Answer: {result2['final_answer']}")
print(f"Intent: {result2['intent']}")  # Should be "direct"
```

## What to Test

### 1. Intent Classification

Test that the planner correctly routes queries:

**RAG Path Queries** (should use `intent="rag"`):

- "What does the document say about X?"
- "Summarize the main topics"
- "Find information about Y"
- "What are the key points in the document?"

**Direct Path Queries** (should use `intent="direct"`):

- "What is machine learning?"
- "Explain quantum computing"
- "How does Python work?"
- General conversational questions

### 2. RAG Functionality

When using RAG path, verify:

- ✅ Documents are retrieved from Qdrant
- ✅ Answer includes citations `[1]`, `[2]`, etc.
- ✅ `retrieved_docs` contains document data with scores
- ✅ Answer is relevant to the query

### 3. Direct Answer Functionality

When using direct path, verify:

- ✅ Answer is generated without retrieval
- ✅ `retrieved_docs` is empty
- ✅ Answer is coherent and relevant

### 4. Error Handling

Test error scenarios:

- Missing API keys → Should show clear error
- Empty collection → Should handle gracefully
- Invalid query → Should return error in state

## Troubleshooting

### "GROQ_API_KEY not found"

```bash
# Set in .env file
echo "GROQ_API_KEY=your-key" >> .env

# Or export
export GROQ_API_KEY=your-key
```

### "Collection does not exist"

- Make sure documents are indexed first
- Check collection name matches
- List collections: `python -c "from qdrant_client import QdrantClient; import os; c = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY')); print(c.get_collections())"`

### "No documents retrieved"

- Verify documents are indexed in the collection
- Check query relevance
- Try increasing `ARTEMIS_RETRIEVAL_K` in config

### Low Confidence Scores

- Normal for ambiguous queries
- Agent defaults to RAG path on low confidence
- Check planner node logs for reasoning

## Expected Test Results

### Successful Test Output

```
✅ Answer: [Generated answer text]
📊 Agent State:
   Intent: rag
   Confidence: 0.87
   Retrieved Docs: 5
   Top document score: 0.8234
```

### Test Checklist

- [ ] Environment variables are set
- [ ] Qdrant connection works
- [ ] Documents are indexed
- [ ] Agent CLI runs without errors
- [ ] RAG queries retrieve documents
- [ ] Direct queries don't retrieve documents
- [ ] Intent classification works correctly
- [ ] Answers include citations (for RAG)
- [ ] Error handling works

## Next Steps

After successful testing:

- Explore [Agent Quick Start Guide](AGENT_QUICKSTART.md) for advanced usage
- Customize configuration via environment variables
- Integrate agent into your own applications
- Check [Architecture Flow](../ARCHITECTURE_FLOW.md) for system overview
