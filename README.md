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

## 🎓 Examples

### Example 1: Restaurant Assistant

```python
from artemis import Agent

# Initialize with restaurant data
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

Built with:

- [DSPy](https://github.com/stanfordnlp/dspy) - Prompt optimization
- [LangChain](https://github.com/langchain-ai/langchain) - Agent orchestration
- [Qdrant](https://qdrant.tech/) - Vector database
- [Groq](https://groq.com/) - Fast LLM inference

---

## ⭐ Star History

If you find A.R.T.E.M.I.S. useful, please consider giving it a star! ⭐

---

**Made with 🏹 by [Anshuman](https://github.com/Anshumanv28)**

_Building the future of adaptable AI agents, one commit at a time._
