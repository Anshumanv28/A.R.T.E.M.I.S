# A.R.T.E.M.I.S. 🏹

**Adaptive Retrieval & Tool-Enabled Multimodal Intelligence System**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **A production-ready, adaptable AI agent framework that learns from your data and integrates with your tools—minimal configuration required.**

---

## 🎯 What is A.R.T.E.M.I.S.?

A.R.T.E.M.I.S. is an **adaptive, generalizable AI agent/chatbot framework** designed for developers who need intelligent assistants that can:

- **🔧 Adapt to any domain** - Automatically learn from your data and use-case context
- **🛠️ Integrate tools dynamically** - Add new tools via YAML/OpenAPI with minimal configuration
- **🧠 Remember context** - Built-in semantic memory for long-term conversations
- **🎨 Support multimodal inputs** - Text, voice, and vision capabilities out of the box
- **⚡ Production-ready** - Optimized with DSPy, powered by LangGraph orchestration

**Perfect for developers** who want a pre-built, adaptable chatbot that can be integrated into any project without extensive customization.

---

## ✨ MVP Features (Phase 1)

### 🎯 Core 4 - Out of the Box

1. **Adaptive RAG** - DSPy-optimized retrieval (90%+ recall)
2. **Agent Orchestration** - LangGraph multi-step planning
3. **Multimodal Inputs** - Text, voice (LiveKit), vision
4. **Semantic Memory** - Short-term conversation context

**Note**: Data chunking is intentionally skipped in MVP since we're working with small datasets. Chunking will be added in Phase 2 for handling larger datasets efficiently.

## 🚀 Coming Soon (Phase 2-3)

- **Dynamic Tool Registry** - Documentation-driven tool registration (YAML/OpenAPI). Tools automatically registered/unregistered as they're added/removed on the backend
- **Advanced Vector Memory** - Qdrant semantic search for long-term context
- **Data Chunking** - Intelligent text chunking for large datasets e.g faqs, reviews, menu (currently skipped for small datasets)
- **Document Schema Converters** - Additional schema types for different use cases:
  - ✅ **RESTAURANT** - Available now (MVP)
  - 🔜 **TRAVEL** - Travel planning (cities, attractions, hotels) - Phase 2
  - 🔜 **SUPPORT** - FAQ/support tickets - Phase 2
  - 🔜 **ECOMMERCE** - Product catalogs - Phase 2
- **Frontend Dashboard** - React interface with tool selection (checkboxes/selectable boxes), configuration, memory management, and page navigation
- **FastAPI Backend APIs** - Production-ready REST APIs for tools and memory
- **Fine-Tuned Custom LLM** - Custom Llama3 70B model fine-tuned for your use-cases
- **Monetized SDK Tier** - Paid tier with premium features (advanced memory, custom models)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Groq API Key](https://console.groq.com/) (free tier available)
- [Qdrant Cloud](https://cloud.qdrant.io/) account (free tier available)

### Installation

```bash
# Clone the repository
git clone https://github.com/Anshumanv28/ARTEMIS.git
cd ARTEMIS

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GROQ_API_KEY="your-groq-api-key"
export QDRANT_URL="your-qdrant-url"
export QDRANT_API_KEY="your-qdrant-api-key"
```

### Basic Usage

```python
from artemis import Agent

# Initialize agent with your data
agent = Agent(
    data_path="./your-data/",
    use_case="restaurant"  # or "travel", "e-commerce", etc.
)

# Chat with the agent
response = agent.chat("What are your restaurant recommendations?")
print(response)

# Add a new tool dynamically
agent.add_tool_from_yaml("tools/weather_api.yaml")

# Use the new tool
response = agent.chat("What's the weather like today?")
```

---

## 📖 Use Cases

A.R.T.E.M.I.S. adapts to any domain with minimal configuration:

| Use Case                 | Description                               | Example                           |
| ------------------------ | ----------------------------------------- | --------------------------------- |
| **Customer Support**     | Intelligent chatbot for your product      | "How do I reset my password?"     |
| **E-commerce Assistant** | Product recommendations and queries       | "Show me laptops under $1000"     |
| **Travel Agent**         | Trip planning and booking assistance      | "Plan a 3-day trip to Paris"      |
| **Restaurant Guide**     | Menu recommendations and reservations     | "Find Italian restaurants nearby" |
| **Internal Tools**       | Company-specific knowledge base assistant | "What's our refund policy?"       |

**Just provide your data** - A.R.T.E.M.I.S. learns the rest.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   A.R.T.E.M.I.S. Agent                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Multimodal │  │  RAG Engine  │  │   Tool       │   │
│  │   Inputs     │→ │  (DSPy)      │→ │   Registry   │   │
│  │              │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                 │                   │          │
│         │                 │         ┌─────────▼──────┐   │
│         │                 │         │ Documentation  │   │
│         │                 │         │ Watcher        │   │
│         │                 │         │ (YAML/OpenAPI)│   │
│         │                 │         └────────────────┘   │
│         └─────────────────┼───────────────────┘          │
│                           │                               │
│                  ┌────────▼────────┐                      │
│                  │  LangGraph      │                      │
│                  │  Orchestrator   │                      │
│                  └────────┬────────┘                      │
│                           │                               │
│                  ┌────────▼────────┐                      │
│                  │  Qdrant Memory │                      │
│                  │  (Semantic)     │                      │
│                  └─────────────────┘                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 🔧 Dynamic Tool Registry Architecture

The tool registry uses a **documentation-driven approach** for maximum reliability:

1. **Backend File Watcher**: Monitors `tools/` directory for YAML/OpenAPI files
2. **Automatic Registration**: When a new tool file is added, it's automatically parsed and registered
3. **Automatic Unregistration**: When a tool file is removed, it's automatically unregistered
4. **No Code Changes Required**: Tools are discovered and integrated without modifying agent code
5. **Frontend UI**: React dashboard provides checkboxes/selectable boxes to enable/disable tools
6. **Page Navigation**: Multi-page interface for tools, memory, and configuration management

**Benefits:**

- ✅ Most reliable approach - tools defined as documentation, not code
- ✅ Hot-reload capability - add/remove tools without restarting
- ✅ Version control friendly - tool definitions are files, not database entries
- ✅ Easy integration - just drop YAML/OpenAPI files in the tools directory

### Tech Stack

- **Core**: DSPy (optimization) + LangChain/LangGraph (orchestration)
- **LLM**: Groq Llama3 70B (MVP) → Custom fine-tuned model (Phase 3)
- **Vector DB**: Qdrant (free tier → scalable)
- **Multimodal**: LiveKit (voice/vision)
- **Backend**: FastAPI
- **Frontend**: React dashboard

---

## 📦 Installation & Setup

### Option 1: From Source

```bash
git clone https://github.com/Anshumanv28/ARTEMIS.git
cd ARTEMIS
pip install -e .
```

### Option 2: Docker (Coming Soon)

```bash
docker-compose up
```

### Configuration

Create a `.env` file:

```env
GROQ_API_KEY=your-groq-api-key
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key
LIVEKIT_URL=your-livekit-url  # Optional
LIVEKIT_API_KEY=your-livekit-api-key  # Optional
```

---

## 🔧 Dynamic Tool Registry

A.R.T.E.M.I.S. uses a **documentation-driven tool registry** - the most reliable approach for dynamic tool management.

### How It Works

1. **File-Based Discovery**: Tools are defined as YAML or OpenAPI specification files in the `tools/` directory
2. **Automatic Registration**: Backend file watcher automatically detects new tool files and registers them
3. **Automatic Unregistration**: Removing a tool file automatically unregisters it from the agent
4. **No Code Changes**: Add or remove tools without modifying any Python code
5. **Frontend Control**: React dashboard provides UI to enable/disable registered tools

### Backend Implementation

```python
# tools/weather_api.yaml
name: get_weather
description: Get current weather for a location
endpoint: https://api.weather.com/v1/current
method: GET
parameters:
  - name: location
    type: string
    required: true
    description: City name or coordinates

# Backend automatically:
# 1. Watches tools/ directory
# 2. Parses YAML/OpenAPI files
# 3. Registers tools with LangChain
# 4. Makes them available to the agent
```

### Frontend Features

- **Tool Selection UI**: Checkboxes or selectable boxes to enable/disable tools
- **Multi-Page Navigation**: Separate pages for tools, memory, and configuration
- **Real-Time Updates**: UI reflects tool registration/unregistration in real-time
- **Tool Status**: Visual indicators for active/inactive tools

**Why Documentation-Driven?**

- ✅ Most reliable - tools are version-controlled files
- ✅ Hot-reload - no restart required
- ✅ Easy integration - just drop files in directory
- ✅ Standard formats - YAML/OpenAPI are well-documented
- ✅ Frontend flexibility - UI can enable/disable without backend changes

---

## 🔌 Document Converters

A.R.T.E.M.I.S. provides flexible document conversion with three levels of control: auto-detect (zero config), built-in schemas, and custom schemas.

### 1. Auto-Detect Mode (Zero Config)

Works with any CSV - automatically uses all column headers:

```python
from artemis.rag import csv_to_documents

# Works with any CSV structure - auto-detects headers (in-memory, default)
docs, metadata = csv_to_documents("any_file.csv")
```

**What it does:**

- Takes all columns from your CSV
- Uses column names as labels
- Produces documents like: `"CustomerID: 123. City: Delhi. Plan: Premium. ..."`
- Returns in-memory lists (fast, simple)
- Perfect for quick experiments, no configuration needed

### 2. Built-in Schemas (Optimized)

Use the pre-built RESTAURANT schema for optimized restaurant data:

```python
from artemis.rag import csv_to_documents, DocumentSchema

# Uses optimized restaurant converter with proper field handling
docs, metadata = csv_to_documents("restaurants.csv", DocumentSchema.RESTAURANT)
```

The RESTAURANT schema includes:

- Smart field normalization (Yes/No handling)
- Location string formatting
- Rating and cost formatting
- Optimized metadata for filtering

### 3. Custom Schemas (Full Control)

Define your own schema converter to control exactly which columns are used, how they're labeled, and how documents are formatted:

```python
from artemis.rag.core.document_converter import register_schema, DocumentSchema, csv_to_documents, format_doc
import pandas as pd

# Define your custom schema
class MySchema(DocumentSchema):
    CUSTOMER = "customer"

@register_schema(MySchema.CUSTOMER)
def convert_customers(csv_path: str):
    """Custom converter with selected columns and formatting."""
    df = pd.read_csv(csv_path)
    docs, metadata = [], []

    for _, row in df.iterrows():
        # Pick only the columns you want
        # Control labels and phrasing
        doc_parts = {
            "Customer": str(row.get("name", "")).strip(),
            "City": str(row.get("city", "")).strip(),
            "Plan": str(row.get("plan", "")).strip(),
        }
        doc = format_doc(doc_parts)
        docs.append(doc)

        # Build whatever metadata you need for filtering
        metadata.append({
            "id": row.get("id"),
            "city": row.get("city"),
            "plan": row.get("plan")
        })

    return docs, metadata

# Use your custom schema
docs, meta = csv_to_documents("customers.csv", MySchema.CUSTOMER)
```

**What you control:**

- ✅ **Which columns** to include (skip irrelevant ones)
- ✅ **How to label** them (custom field names)
- ✅ **How to format** (combine fields, add context)
- ✅ **Metadata structure** (what to store for filtering)

### When to Use Each Approach

| Approach            | Use When                                                           | Example                                                          |
| ------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| **Auto-detect**     | Quick experiments, unknown CSV structure                           | `csv_to_documents("data.csv")`                                   |
| **Built-in schema** | Using restaurant data                                              | `csv_to_documents("restaurants.csv", DocumentSchema.RESTAURANT)` |
| **Custom schema**   | Need specific columns, custom formatting, or domain-specific logic | Register your own converter                                      |

### Advanced: File-Based Storage (For Testing/Large Datasets)

By default, documents are returned **in-memory** (fast and simple). For unit testing or very large datasets, you can save documents to files:

```python
# File-based mode (saves to artemis_data/docs/ folder)
doc_paths, metadata_path = csv_to_documents("data.csv", save_to_disk=True)

# Files are automatically deleted after ingestion by retriever
retriever.add_documents(doc_paths, metadata_path)
```

**Or set via environment variable:**

```bash
# In .env file or export
ARTEMIS_SAVE_DOCS_TO_DISK=true
```

**When to use file-based mode:**

- Unit testing (can inspect files before ingestion)
- Very large datasets (avoids memory issues)
- Debugging (files remain if ingestion fails)

**Default:** In-memory mode (faster for small/medium datasets)

**Note:** Generated files are stored in `artemis_data/docs/` and logs in `artemis_data/logs/`. These folders are automatically created and ignored by Git.

### The format_doc Helper

All converters use the `format_doc()` helper for consistent formatting:

```python
from artemis.rag import format_doc

doc_parts = {
    "Product": "Laptop",
    "Price": "$999",
    "In Stock": "Yes",
}

document = format_doc(doc_parts)
# Returns: "Product: Laptop. Price: $999. In Stock: Yes."
```

**Note:** Auto-detect works great for MVP and quick experiments. Custom schemas give you full control when you need optimized document quality for production use.

---

## 🔍 Retrieval System

A.R.T.E.M.I.S. uses a **modular retrieval architecture** with separated indexing and retrieval components, enabling extensible search strategies via a registry pattern.

### Architecture Overview

The retrieval system is split into two main components:

1. **`Indexer`** - Handles document storage, embedding generation, and Qdrant operations
2. **`Retriever`** - Handles document retrieval using registered search strategies

This separation enables:

- Independent testing of indexing and retrieval
- Shared resources between components
- Extensible search strategies via decorator registration

### Basic Usage

```python
from artemis.rag import Indexer, Retriever, RetrievalMode

# Option 1: Separate indexing and retrieval (recommended)
indexer = Indexer(collection_name="restaurants")
indexer.add_documents(docs, metadata)

retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    indexer=indexer  # Share resources
)
results = retriever.retrieve("Italian restaurants", k=5)

# Option 2: Retriever with explicit embedder (for retrieval-only use)
from artemis.rag import Embedder
embedder = Embedder()  # Uses default model, or Embedder(model_name="...")
retriever = Retriever(mode=RetrievalMode.SEMANTIC, embedder=embedder)
results = retriever.retrieve("Italian restaurants", k=5)

# Note: For adding documents, use Indexer. Retriever.add_documents() is for
# backward compatibility only - it creates an Indexer internally.
```

### Retrieval Modes

A.R.T.E.M.I.S. supports multiple retrieval modes:

- **`SEMANTIC`** (MVP) - Semantic vector search using embeddings
- **`KEYWORD`** (Coming Soon) - BM25/TF-IDF keyword-based search
- **`HYBRID`** (Coming Soon) - Combined semantic + keyword search

### Extending with Custom Retrieval Strategies

You can register custom retrieval strategies using the `@register_strategy` decorator. Strategies are organized in the `artemis/rag/strategies/` folder, similar to document converters.

#### Built-in Strategies

- **`semantic.py`** - Semantic vector search (MVP, primary strategy)
- **`keyword.py`** - Keyword search placeholder (Phase 2)
- **`hybrid.py`** - Hybrid search placeholder (Phase 2)

#### Creating a Custom Strategy

1. **Create a new strategy file** in `artemis/rag/strategies/`:

```python
# artemis/rag/strategies/my_custom_strategy.py
from typing import List, Dict, Any
from artemis.rag.core.retriever import register_strategy, RetrievalMode, Retriever
from artemis.utils import get_logger

logger = get_logger(__name__)

@register_strategy(RetrievalMode.KEYWORD)  # Or create a new RetrievalMode
def my_custom_keyword_search(retriever: Retriever, query: str, k: int) -> List[Dict[str, Any]]:
    """
    Custom keyword search implementation.

    Args:
        retriever: Retriever instance (provides access to qdrant_client, etc.)
        query: Search query string
        k: Number of results to return

    Returns:
        List of dictionaries with 'text', 'score', and 'metadata' keys
    """
    # Your custom BM25 or keyword search logic here
    # Access retriever.qdrant_client, retriever.collection_name, etc.
    results = []
    # ... implementation ...
    return results
```

2. **Import it in `artemis/rag/strategies/__init__.py`**:

```python
# artemis/rag/strategies/__init__.py
try:
    from artemis.rag.strategies.my_custom_strategy import my_custom_keyword_search
except ImportError:
    pass
```

3. **Use your custom strategy**:

```python
from artemis.rag import Retriever, RetrievalMode

retriever = Retriever(mode=RetrievalMode.KEYWORD)
results = retriever.retrieve("Italian food", k=5)
```

**Note:** See `artemis/rag/strategies/example_custom.py` for a complete example template.

### Why Multiple Search Strategies?

Different retrieval modes excel in different scenarios:

- **Semantic Search**: Best for natural-language, fuzzy queries (e.g., "restaurants with good ambiance")
- **Keyword Search**: Best when exact terms matter (e.g., API names, IDs, legal citations)
- **Hybrid Search**: Combines both for improved relevance and robustness

This design makes A.R.T.E.M.I.S. suitable for diverse use cases:

- **Dev Assistant** → Keyword/hybrid for exact API names
- **Legal/Compliance Bot** → BM25/hybrid for precise citations
- **Enterprise Search** → Hybrid for varied query types

---

## 🎓 Examples

### Example 1: Restaurant Assistant

```python
from artemis import Agent

# Initialize with restaurant data
# Note: Uses Kaggle restaurant dataset (see Acknowledgments section)
agent = Agent(
    data_path="./data/restaurants/",
    use_case="restaurant"
)

# Natural conversation
response = agent.chat("I'm craving Italian food. Any recommendations?")
# Agent retrieves relevant restaurant data and responds contextually
```

### Example 2: Adding Custom Tools (Documentation-Driven)

```python
# Tools are automatically discovered from documentation files
# Backend watches for YAML/OpenAPI files and registers/unregisters dynamically

# Option 1: YAML tool definition
# tools/weather.yaml
name: get_weather
description: Get current weather for a location
endpoint: https://api.weather.com/v1/current
method: GET
parameters:
  - name: location
    type: string
    required: true

# Option 2: OpenAPI spec
# tools/api_spec.yaml (OpenAPI 3.0 format)
# The registry automatically parses and registers all endpoints

# Tools are automatically available once files are added to the tools directory
agent.chat("What's the weather in New York?")
# Agent automatically uses the registered weather tool
```

### Example 2b: Frontend Tool Management

```typescript
// React Dashboard - Tool Selection UI
// Users can enable/disable tools via checkboxes or selectable boxes
<ToolSelector>
  <CheckboxTool name="weather_api" enabled={true} />
  <CheckboxTool name="calendar_api" enabled={false} />
  <CheckboxTool name="payment_api" enabled={true} />
</ToolSelector>

// Navigation between different pages (later stages)
<Navigation>
  <Page name="tools" />
  <Page name="memory" />
  <Page name="configuration" />
</Navigation>
```

### Example 3: Multi-Use Case Switching

```python
# Start with restaurant data
agent = Agent(data_path="./data/restaurants/", use_case="restaurant")
agent.chat("Find me a pizza place")

# Switch to travel domain
agent.adapt_to_new_use_case(
    data_path="./data/travel/",
    use_case="travel"
)
agent.chat("Plan a trip to Tokyo")
```

---

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Running the Dashboard

```bash
cd frontend
npm install
npm start
```

### Building Documentation

```bash
mkdocs serve
```

---

## 📊 Roadmap

### Phase 1: MVP Core (Weeks 1-4) ✅ In Progress

**Core 4 Features - Available Now:**

- [x] **Adaptive RAG** - DSPy-optimized retrieval (90%+ recall)
- [x] **Agent Orchestration** - LangGraph multi-step planning
- [ ] **Multimodal Inputs** - Text, voice (LiveKit), vision
- [ ] **Semantic Memory** - Short-term conversation context

### Phase 2: Adaptation & Features (Weeks 5-7) 🚀 Coming Soon

- [ ] **Dynamic Tool Registry** - Documentation-driven (YAML/OpenAPI file watcher)
- [ ] **Frontend Tool Management UI** - Checkboxes/selectable boxes for tool selection
- [ ] **Advanced Vector Memory** - Qdrant semantic search for long-term context
- [ ] **FastAPI Backend** - Tool registration/unregistration APIs
- [ ] **React Dashboard** - Multi-page navigation (tools, memory, config)

### Phase 3: Custom LLM & Monetization (Weeks 8-12) 🚀 Coming Soon

- [ ] **Fine-Tuned Custom LLM** - Llama3 70B model fine-tuned for use-cases
- [ ] **vLLM Deployment** - Cloud inference hosting
- [ ] **SDK Distribution** - Python package distribution
- [ ] **Monetized SDK Tier** - Paid tier with premium features

See [ROADMAP.md](./ROADMAP.md) for detailed progress.

---

## 🤝 Contributing

We welcome contributions! A.R.T.E.M.I.S. is built for the community.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 🎯 Future: SDK Distribution

A.R.T.E.M.I.S. will be distributed as a **Python SDK** for easy integration:

```bash
pip install artemis-sdk
```

**Planned SDK Features:**

- One-line installation
- Pre-configured templates for common use-cases
- Cloud-hosted memory (optional)
- Premium features (advanced memory, custom models)

**Monetization**: Free tier for open-source use, paid tier for enterprise features.

---

## 📞 Support & Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/Anshumanv28/ARTEMIS/issues)
- **Discussions**: [Join the community](https://github.com/Anshumanv28/ARTEMIS/discussions)
- **Documentation**: [Full docs](https://artemis.readthedocs.io) (coming soon)

---

## 🙏 Acknowledgments

### Datasets

- **Restaurant Dataset** - Used for MVP testing and examples
  - Dataset: [Restaurant Dataset](https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset) by [mohdshahnawazaadil](https://www.kaggle.com/mohdshahnawazaadil)
  - License: Please refer to the dataset's license on Kaggle
  - Used for: Document conversion examples, RAG testing, and retrieval strategy validation

### Libraries & Tools

Built with:

- [DSPy](https://github.com/stanfordnlp/dspy) - Prompt optimization
- [LangChain](https://github.com/langchain-ai/langchain) - Agent orchestration
- [Qdrant](https://qdrant.tech/) - Vector database
- [Groq](https://groq.com/) - Fast LLM inference
- [KaggleHub](https://github.com/Kaggle/kagglehub) - Dataset downloading and management

---

## ⭐ Star History

If you find A.R.T.E.M.I.S. useful, please consider giving it a star! ⭐

---

**Made with 🏹 by [Anshuman](https://github.com/Anshumanv28)**

_Building the future of adaptable AI agents, one commit at a time._
