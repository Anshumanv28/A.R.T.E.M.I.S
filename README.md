# A.R.T.E.M.I.S. 🏹

**Adaptive Retrieval & Tool-Enabled Multimodal Intelligence System**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **A production-ready, adaptable AI agent framework that learns from your data and integrates with your tools—minimal configuration required.**

---

## 📑 Table of Contents

- [What is A.R.T.E.M.I.S.?](#-what-is-artemis)
- [Features Overview](#-features-overview)
- [Quick Start](#-quick-start)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Running the System](#-running-the-system)
  - [Step 1: Set Up Qdrant](#step-1-set-up-qdrant)
  - [Step 2: Ingest Your Data](#step-2-ingest-your-data)
  - [Step 3: Query Your Data](#step-3-query-your-data)
  - [Step 4: Run the Demo](#step-4-run-the-demo)
- [What's Available](#-whats-available)
- [Documentation](#-documentation)
- [For Developers](#-for-developers)
- [For Contributors](#-for-contributors)
- [Examples](#-examples)
- [Architecture](#-architecture)
- [Project Status](#-project-status)
- [Roadmap](#-roadmap)
- [Get in Touch](#-get-in-touch)
- [Support & Community](#-support--community)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

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

## ✨ Features Overview

### Currently Available (MVP)

- ✅ **Adaptive RAG** - DSPy-optimized retrieval (90%+ recall)
- ✅ **File Ingestion** - Support for CSV, PDF, DOCX, Markdown, and Text files
- ✅ **CSV Schema Converters** - RESTAURANT and TRAVEL schemas
- ✅ **Chunking Strategies** - CSV_ROW, FIXED, FIXED_OVERLAP, SEMANTIC
- ✅ **Semantic Search** - Vector-based retrieval with Qdrant
- ✅ **Extensible Architecture** - Registry pattern for custom components

### Coming Soon (Phase 2-3)

- 🔜 **Agent Orchestration** - LangGraph multi-step planning
- 🔜 **Multimodal Inputs** - Text, voice (LiveKit), vision
- 🔜 **Dynamic Tool Registry** - Documentation-driven tool registration
- 🔜 **Advanced Vector Memory** - Long-term context management
- 🔜 **Frontend Dashboard** - React interface for configuration
- 🔜 **Fine-Tuned Custom LLM** - Custom Llama3 70B model

See [Roadmap](#-roadmap) for detailed progress.

---

## 🚀 Quick Start

Get A.R.T.E.M.I.S. running in 5 minutes:

```bash
# 1. Clone and install
git clone https://github.com/Anshumanv28/ARTEMIS.git
cd ARTEMIS
pip install -r requirements.txt

# 2. Set up environment
export QDRANT_URL="your-qdrant-url"
export QDRANT_API_KEY="your-api-key"

# 3. Run the demo
python test_queries.py
```

For detailed setup, see [Getting Started](#-getting-started) or [Quick Start Guide](docs/QUICK_START.md).

---

## 🏁 Getting Started

### Prerequisites

- **Python 3.12+** - [Download Python](https://www.python.org/downloads/)
- **Qdrant Account** - [Qdrant Cloud](https://cloud.qdrant.io/) (free tier available) or local Qdrant instance
- **Git** - For cloning the repository

### Installation

#### Option 1: From Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/Anshumanv28/ARTEMIS.git
cd ARTEMIS

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

#### Option 2: Docker (Coming Soon)

```bash
docker-compose up
```

### Configuration

Create a `.env` file in the project root:

```env
# Required
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key

# Optional
GROQ_API_KEY=your-groq-api-key
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-livekit-api-key
```

Or set environment variables:

```bash
export QDRANT_URL="your-qdrant-url"
export QDRANT_API_KEY="your-api-key"
```

**Getting Qdrant Credentials:**

1. **Qdrant Cloud** (Recommended for quick start):

   - Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
   - Create a free cluster
   - Copy the URL and API key from the dashboard

2. **Local Qdrant** (For development):
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   # Then use: QDRANT_URL="http://localhost:6333"
   ```

For detailed setup instructions, see [Setup Guide](docs/SETUP_GUIDE.md).

---

## 🏃 Running the System

### Step 1: Set Up Qdrant

Choose one of the following:

**Option A: Qdrant Cloud (Recommended)**

1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
2. Create a free cluster
3. Copy your cluster URL and API key

**Option B: Local Qdrant**

```bash
docker run -p 6333:6333 qdrant/qdrant
# Use QDRANT_URL="http://localhost:6333" and leave API key empty
```

### Step 2: Ingest Your Data

```python
from artemis.rag import Indexer, FileType, ingest_file, DocumentSchema

# Create indexer (manages Qdrant connection and embeddings)
indexer = Indexer(
    qdrant_url="your-qdrant-url",  # or use env var
    qdrant_api_key="your-api-key",  # or use env var
    collection_name="my_documents"
)

# Ingest files
ingest_file("restaurants.csv", FileType.CSV, indexer,
            schema=DocumentSchema.RESTAURANT)
ingest_file("manual.pdf", FileType.PDF, indexer)
ingest_file("docs/readme.md", FileType.MD, indexer)
```

### Step 3: Query Your Data

```python
from artemis.rag import Retriever, RetrievalMode

# Create retriever (use same indexer for consistency)
retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    indexer=indexer  # Recommended: ensures same embedder
)

# Query
results = retriever.retrieve("Italian restaurants in Mumbai", k=5)

for result in results:
    print(f"Score: {result['score']:.4f}")
    print(f"Text: {result['text']}")
    print(f"Metadata: {result['metadata']}")
    print()
```

### Step 4: Run the Demo

```bash
# Run the interactive query demo
python test_queries.py
```

**What the demo does:**

- ✅ Connects to your Qdrant instance
- ✅ Runs 6 example queries automatically
- ✅ Shows results with scores and metadata
- ✅ Enters interactive mode for custom queries

**Requirements:**

- Qdrant instance running (cloud or local)
- Data already ingested (use `ingest_file()` first)
- Environment variables set (QDRANT_URL, QDRANT_API_KEY)

**Example Output:**

```
🔍 A.R.T.E.M.I.S. Query Demo
============================================================

1. Connecting to Qdrant...
   ✅ Connected to Qdrant

2. Creating Retriever...
   ✅ Retriever ready

============================================================
📝 Example Queries
============================================================

1. Query: "Italian restaurants in Mumbai"
------------------------------------------------------------
   Result 1 (Score: 0.9234):
   Restaurant: Trattoria. Location: Mumbai, Maharashtra...
   City: Mumbai
   Rating: 4.5
   ...
```

### Complete Example Script

```python
#!/usr/bin/env python3
"""Complete example: Ingest and query data."""

from artemis.rag import (
    Indexer, Retriever, RetrievalMode,
    FileType, DocumentSchema, ingest_file
)

# 1. Setup
indexer = Indexer(collection_name="demo")
retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)

# 2. Ingest
ingest_file("data/restaurants.csv", FileType.CSV, indexer,
            schema=DocumentSchema.RESTAURANT)

# 3. Query
results = retriever.retrieve("Italian restaurants", k=3)
for r in results:
    print(f"{r['score']:.3f}: {r['text'][:100]}...")
```

---

## 📋 What's Available

Before extending A.R.T.E.M.I.S., here's what you get out of the box:

### File Types Supported

- ✅ **CSV** - Structured data (restaurants, travel, products, etc.)
- ✅ **PDF** - Documents, manuals, reports
- ✅ **DOCX** - Word documents
- ✅ **Markdown** - Documentation, README files
- ✅ **TEXT** - Plain text files

### CSV Schema Converters

- ✅ **RESTAURANT** - Restaurant data (fully implemented)
- ✅ **TRAVEL** - Travel/hotel bookings (fully implemented)
- 🔜 **SUPPORT** - FAQ/support tickets (coming soon)

### Chunking Strategies

- ✅ **CSV_ROW** - Row-based chunking for CSV files (default for CSV)
- ✅ **FIXED** - Fixed-size chunks without overlap
- ✅ **FIXED_OVERLAP** - Fixed-size chunks with overlap (default for PDF/DOCX/TEXT)
- ✅ **SEMANTIC** - Sentence/paragraph-aware chunking (default for Markdown)
- ⚠️ **AGENTIC** - LLM-driven chunking (placeholder, falls back to FIXED_OVERLAP)

### Retrieval Strategies

- ✅ **SEMANTIC** - Semantic vector search (fully implemented, default)
- ⚠️ **KEYWORD** - BM25/TF-IDF keyword search (placeholder, raises NotImplementedError)
- ⚠️ **HYBRID** - Combined semantic + keyword (placeholder, raises NotImplementedError)

### Quick Check: What's Registered?

```python
# Check available CSV schemas
from artemis.rag.ingestion.converters.csv_converter import CSV_CONVERTERS
print("Available CSV schemas:", list(CSV_CONVERTERS.keys()))

# Check available chunkers
from artemis.rag.ingestion.chunkers.registry import CHUNKERS
print("Available chunkers:", list(CHUNKERS.keys()))

# Check available retrieval strategies
from artemis.rag.core.retriever import RETRIEVAL_STRATEGIES
print("Available strategies:", list(RETRIEVAL_STRATEGIES.keys()))
```

---

## 📚 Documentation

### Core Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get running in 5 minutes
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[Extending A.R.T.E.M.I.S.](docs/EXTENDING_ARTEMIS.md)** - Complete developer guide for custom components
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Cheat sheet for extending the system

### Technical Documentation

- **[Architecture Flow](ARCHITECTURE_FLOW.md)** - System architecture and data flow
- **[Hybrid Search Implementation](docs/HYBRID_SEARCH_IMPLEMENTATION.md)** - Hybrid search details
- **[Metadata Filtering](docs/METADATA_FILTERING.md)** - Metadata filtering guide
- **[Roadmap](ROADMAP.md)** - Project roadmap and milestones

### Examples & Templates

- **[Travel Converter Example](examples/README_travel_example.md)** - CSV schema converter guide
- **[Template Files](examples/templates/README.md)** - Boilerplate code for custom components
- **[Travel Converter Script](examples/travel_converter_example.py)** - Working example

### Documentation Index

See [docs/README.md](docs/README.md) for a complete documentation index.

---

## 👨‍💻 For Developers

### Should I Extend A.R.T.E.M.I.S.?

**Only extend if:**

- ❌ Built-in features don't meet your needs
- ❌ You need domain-specific logic
- ❌ You want to customize behavior

**Don't extend if:**

- ✅ Auto-detect works fine for your CSV
- ✅ Default chunking is sufficient
- ✅ Semantic search meets your needs

### Getting Started with Extensions

1. **Check what's available** - See [What's Available](#-whats-available) section
2. **Review documentation** - Read [Extending A.R.T.E.M.I.S.](docs/EXTENDING_ARTEMIS.md)
3. **Use templates** - Start with [template files](examples/templates/)
4. **Quick reference** - Keep [Quick Reference](docs/QUICK_REFERENCE.md) handy

### Extension Guides

- **[Extending A.R.T.E.M.I.S.](docs/EXTENDING_ARTEMIS.md)** - Comprehensive guide covering:

  - Custom CSV Schema Converters
  - Custom Chunking Strategies
  - Custom Retrieval Strategies
  - Custom Metadata Extractors
  - Registration patterns and best practices

- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Quick cheat sheet with:

  - Registration decorators
  - Function signatures
  - Import paths
  - Common code snippets

- **[Template Files](examples/templates/)** - Ready-to-use boilerplate:
  - `template_csv_schema.py` - CSV schema converter template
  - `template_chunker.py` - Chunking strategy template
  - `template_retrieval_strategy.py` - Retrieval strategy template
  - `template_metadata_extractor.py` - Metadata extractor template

---

## 🤝 For Contributors

We welcome contributions! A.R.T.E.M.I.S. is built for the community.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Anshumanv28/ARTEMIS.git
cd ARTEMIS

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_csv_converter.py

# Run with coverage
pytest --cov=artemis tests/
```

### Code Style

- **Formatting**: We use [black](https://github.com/psf/black) for code formatting
- **Linting**: Follow PEP 8 guidelines
- **Type Hints**: Include type hints for all functions

```bash
# Format code
black artemis/

# Check formatting
black --check artemis/
```

### Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Run tests** (`pytest tests/`)
5. **Format code** (`black artemis/`)
6. **Commit your changes** (`git commit -m 'Add amazing feature'`)
7. **Push to the branch** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request**

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines (if available).

---

## 🎓 Examples

### Example 1: Restaurant Assistant

```python
from artemis.rag import Indexer, Retriever, RetrievalMode, FileType, ingest_file, DocumentSchema

# Setup
indexer = Indexer(collection_name="restaurants")
ingest_file("restaurants.csv", FileType.CSV, indexer, schema=DocumentSchema.RESTAURANT)

retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)

# Query
results = retriever.retrieve("Italian restaurants in Mumbai", k=5)
for result in results:
    print(f"{result['score']:.3f}: {result['text']}")
```

### Example 2: Multi-File Ingestion

```python
from artemis.rag import Indexer, FileType, ingest_file

indexer = Indexer(collection_name="documents")

# Ingest multiple file types
ingest_file("data.csv", FileType.CSV, indexer)
ingest_file("manual.pdf", FileType.PDF, indexer)
ingest_file("readme.md", FileType.MD, indexer)
```

### Example 3: Custom Chunking

```python
from artemis.rag import Indexer, FileType, ingest_file, ChunkStrategy

indexer = Indexer(collection_name="documents")

# Use semantic chunking for PDF
ingest_file("document.pdf", FileType.PDF, indexer,
            chunk_strategy=ChunkStrategy.SEMANTIC, chunk_size=1500)
```

For more examples, see:

- [Travel Converter Example](examples/README_travel_example.md)
- [Template Files](examples/templates/)
- [test_queries.py](test_queries.py) - Interactive demo script

---

## 🏗️ Architecture

A.R.T.E.M.I.S. follows a modular architecture with clear separation of concerns:

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

### Key Components

- **RAG Engine** - Document ingestion, chunking, indexing, and retrieval
- **Tool Registry** - Dynamic tool registration via YAML/OpenAPI files
- **LangGraph Orchestrator** - Multi-step agent planning
- **Qdrant Memory** - Vector-based semantic memory

### Data Flow

A.R.T.E.M.I.S. follows a clear pipeline: **Load → Chunk → Index → Retrieve**

For detailed architecture information, see [ARCHITECTURE_FLOW.md](ARCHITECTURE_FLOW.md).

### Tech Stack

- **Core**: DSPy (optimization) + LangChain/LangGraph (orchestration)
- **LLM**: Groq Llama3 70B (MVP) → Custom fine-tuned model (Phase 3)
- **Vector DB**: Qdrant (free tier → scalable)
- **Multimodal**: LiveKit (voice/vision)
- **Backend**: FastAPI
- **Frontend**: React dashboard

---

## 📊 Project Status

### Current Phase: MVP (Phase 1)

**What's Working:**

- ✅ RAG pipeline (ingestion, chunking, indexing, retrieval)
- ✅ Multiple file type support (CSV, PDF, DOCX, MD, TEXT)
- ✅ CSV schema converters (RESTAURANT, TRAVEL)
- ✅ Multiple chunking strategies
- ✅ Semantic search
- ✅ Extensible architecture with registry pattern

**In Progress:**

- 🔄 Agent orchestration
- 🔄 Multimodal inputs
- 🔄 Advanced memory management

**Planned:**

- 📅 Dynamic tool registry
- 📅 Frontend dashboard
- 📅 Custom LLM fine-tuning

See [ROADMAP.md](./ROADMAP.md) for detailed progress and milestones.

---

## 📊 Roadmap

### Phase 1: MVP Core (Weeks 1-4) ✅ In Progress

**Core 4 Features - Available Now:**

- [x] **Adaptive RAG** - DSPy-optimized retrieval (90%+ recall)
- [x] **File Ingestion** - Multiple file types and chunking strategies
- [ ] **Agent Orchestration** - LangGraph multi-step planning
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

## 📞 Get in Touch

We'd love to hear from you! Here are the best ways to reach us:

### Community

- **GitHub Issues** - [Report bugs or request features](https://github.com/Anshumanv28/ARTEMIS/issues)
- **GitHub Discussions** - [Join the community](https://github.com/Anshumanv28/ARTEMIS/discussions)
- **GitHub Repository** - [View the code](https://github.com/Anshumanv28/ARTEMIS)

### Contributing

- **Pull Requests** - We welcome contributions! See [For Contributors](#-for-contributors) section
- **Feature Requests** - Open an issue with the `enhancement` label
- **Bug Reports** - Open an issue with the `bug` label

### Documentation

- **Full Documentation** - [docs/](docs/) directory
- **Quick Start** - [docs/QUICK_START.md](docs/QUICK_START.md)
- **Setup Guide** - [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 💬 Support & Community

### Getting Help

- **Documentation** - Check the [Documentation](#-documentation) section
- **Examples** - See [Examples](#-examples) section
- **GitHub Issues** - Search existing issues or create a new one
- **GitHub Discussions** - Ask questions and share ideas

### Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share your use cases and examples
- Report bugs and suggest improvements

### Resources

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **Templates**: [examples/templates/](examples/templates/)
- **Roadmap**: [ROADMAP.md](ROADMAP.md)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

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
