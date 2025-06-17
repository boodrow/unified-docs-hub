[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/boodrow-mcp-server-unified-docs-hub-badge.png)](https://mseep.ai/app/boodrow-mcp-server-unified-docs-hub)

# 🚀 Unified Docs Hub - The Ultimate MCP Documentation Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Server](https://img.shields.io/badge/MCP-Server-green)](https://github.com/modelcontextprotocol)

Transform your AI assistant into a documentation powerhouse! Unified Docs Hub is an MCP (Model Context Protocol) server that creates a massive, searchable knowledge base from 170+ curated repositories and 1000+ auto-discovered GitHub projects.

## 🌟 Why Unified Docs Hub?

Ever wished your AI assistant had instant access to ALL the documentation it needs? This MCP server solves that by:

- **📚 Massive Knowledge Base**: 170+ hand-picked repositories + 1000+ auto-discovered popular projects
- **🔍 Lightning-Fast Search**: Full-text search across 11,000+ documentation files in milliseconds
- **🤖 AI-Optimized**: Perfect for Claude, ChatGPT, and other AI assistants using MCP
- **📈 Self-Updating**: Automated daily updates and weekly discovery of new repositories
- **🎯 Specialized Coverage**: Deep expertise in Trading/Finance, AI/ML, DevOps, and 20+ categories

## 🎬 Real-World Examples

### Example 1: Building a Trading Bot
```
AI: "Show me how to build a crypto trading bot with backtesting"

You: unified_search(query="crypto trading bot backtesting", category="Trading & Finance")

Result: Instant access to documentation from:
- Freqtrade (advanced crypto trading bot)
- Backtrader (backtesting framework)
- CCXT (100+ exchange APIs)
- TA-Lib (200+ technical indicators)
```

### Example 2: Learning Kubernetes
```
AI: "Explain Kubernetes deployment strategies"

You: unified_search(query="kubernetes deployment strategies", category="Cloud/DevOps")

Result: Documentation from:
- Official Kubernetes docs
- Helm charts best practices
- ArgoCD GitOps workflows
- Istio service mesh patterns
```

### Example 3: Machine Learning Pipeline
```
AI: "Set up an MLOps pipeline with experiment tracking"

You: unified_search(query="mlops pipeline experiment tracking", category="MLOps")

Result: Comprehensive guides from:
- MLflow (experiment tracking)
- Kubeflow (distributed training)
- DVC (data versioning)
- Weights & Biases (visualization)
```

## 📊 What's Inside?

### Knowledge Coverage

| Category | Repositories | Highlights |
|----------|-------------|------------|
| **Trading & Finance** | 64 repos | Algorithmic trading, options, forex, HFT, portfolio optimization |
| **AI/ML** | 20 repos | LLMs, transformers, deep learning, NLP, computer vision |
| **Cloud/DevOps** | 15 repos | Kubernetes, Docker, Terraform, CI/CD, monitoring |
| **Web Development** | 12 repos | React, Vue, Next.js, full-stack frameworks |
| **MLOps** | 6 repos | ML lifecycle, experiment tracking, model deployment |
| **Data Engineering** | 8 repos | Apache Spark, Airflow, dbt, data pipelines |
| **Observability** | 5 repos | Prometheus, Grafana, OpenTelemetry, APM |
| **Blockchain** | 5 repos | Smart contracts, DeFi, Web3 development |
| **20+ More Categories** | ... | Security, databases, mobile, desktop, and more |

### Key Features

- **🔥 Full-Text Search**: SQLite FTS5 engine for sub-second searches across millions of lines
- **📈 Quality Scoring**: Curated repos ranked by documentation quality (1-10 scale)
- **🏷️ Smart Categorization**: Browse by technology area or programming language
- **🔄 Auto-Discovery**: Continuously finds new popular repositories (10k+ stars)
- **💾 Efficient Storage**: Deduplication and compression keep the database lean
- **🛡️ Rate Limit Handling**: Respects GitHub API limits with smart throttling

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- GitHub Personal Access Token (optional but recommended)
- An MCP-compatible AI assistant (Claude Desktop, Continue.dev, etc.)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/unified-docs-hub.git
cd unified-docs-hub
```

2. **Set up Python environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure your MCP client**

For Claude Desktop, add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "unified-docs-hub": {
      "command": "/path/to/unified-docs-hub/venv/bin/python",
      "args": ["/path/to/unified-docs-hub/unified_docs_hub_server.py"],
      "env": {
        "GITHUB_TOKEN": "your-github-token-here"
      }
    }
  }
}
```

4. **Initial indexing** (optional - the server will do this automatically)
```bash
# Index all curated repositories
python -c "import asyncio; from unified_docs_hub_server import index_repositories; asyncio.run(index_repositories('smart'))"
```

## 📋 Available MCP Tools

### `unified_search`
Search across all documentation with powerful filters.

```python
# Basic search
unified_search("react hooks tutorial")

# Advanced search with filters
unified_search(
    query="transformer architecture attention",
    category="AI/ML",
    min_stars=5000
)

# Trading-specific search
unified_search(
    query="options greeks volatility smile",
    category="Trading & Finance"
)
```

### `index_repositories`
Control repository indexing and discovery.

```python
# Smart mode: Index curated + discover popular (recommended)
index_repositories(mode="smart")

# Update all existing repos
index_repositories(mode="update")

# Discover new trending repos
index_repositories(mode="discover", min_stars=5000, count=50)
```

### `list_repositories`
Browse indexed repositories.

```python
# List all Trading & Finance repos
list_repositories(category="Trading & Finance")

# Show only curated high-quality repos
list_repositories(source="curated", limit=20)
```

### `get_repository_docs`
Get all documentation for a specific repository.

```python
# Get all Kubernetes docs
get_repository_docs("kubernetes/kubernetes")

# Get trading library docs
get_repository_docs("freqtrade/freqtrade")
```

### `get_statistics`
View comprehensive database statistics.

```python
get_statistics()
# Returns: Total repos, documents, categories, languages, API status
```

## 🤖 Automated Updates

The server includes automated indexing that keeps your knowledge base fresh:

### Setup Automated Updates

```bash
# Run the setup script
./setup_automated_indexing.sh

# Or manually start the updater
python automated_index_updater.py --once  # Run once
python automated_index_updater.py          # Run continuously
```

### Update Schedule
- **Daily**: Updates all curated repositories (2 AM, 2 PM)
- **Weekly**: Discovers new trending repositories
- **On-Demand**: Manual updates via MCP tools

## 🏗️ Architecture

### Core Components

```
unified-docs-hub/
├── unified_docs_hub_server.py  # Main MCP server
├── database.py                 # SQLite + FTS5 engine
├── github_client.py            # GitHub API integration
├── response_limiter.py         # HTTP/2 error prevention
├── repositories.yaml           # Curated repo list
├── automated_index_updater.py  # Auto-update system
└── unified_docs.db            # Documentation database
```

### How It Works

1. **Curation**: Hand-picked repositories in `repositories.yaml` with quality scores
2. **Discovery**: Automatically finds popular repos (10k+ stars) via GitHub API
3. **Indexing**: Downloads and indexes README, docs/, and documentation files
4. **Storage**: SQLite with FTS5 for efficient full-text search
5. **Serving**: FastMCP server provides tools for AI assistants
6. **Updates**: Automated system keeps documentation current

## 🎯 Use Cases

### For AI Developers
- Instant access to ML framework documentation
- Compare different approaches across libraries
- Find code examples and best practices

### For Traders & Quants
- Complete algorithmic trading documentation
- Options pricing models and strategies
- Backtesting frameworks and market data APIs

### For DevOps Engineers
- Kubernetes patterns and anti-patterns
- CI/CD pipeline examples
- Infrastructure as Code templates

### For Full-Stack Developers
- Frontend framework comparisons
- Backend architecture patterns
- Database optimization techniques

## 🛠️ Customization

### Adding Custom Repositories

Edit `repositories.yaml`:
```yaml
curated_repositories:
  - repo: "owner/awesome-project"
    category: "Web Development"
    description: "An awesome web framework"
    quality_score: 9
    priority: high
    doc_paths:
      - "docs/"
      - "README.md"
    topics: ["web", "framework", "javascript"]
```

### Creating Custom Categories

Add new categories to group related technologies:
```yaml
  - repo: "quantum-computing/qiskit"
    category: "Quantum Computing"  # New category!
    description: "Quantum computing SDK"
```

## 📈 Expansion Reports

See our journey of building this massive knowledge base:

- [EXPANSION_SUMMARY.md](EXPANSION_SUMMARY.md) - Overview of all expansions
- [TRADING_KNOWLEDGE_BASE_COMPLETE.md](TRADING_KNOWLEDGE_BASE_COMPLETE.md) - Trading & Finance deep dive
- [ULTIMATE_TRADING_EXPANSION.md](ULTIMATE_TRADING_EXPANSION.md) - Final trading expansion details
- [FINAL_EXPANSION_REPORT_2025.md](FINAL_EXPANSION_REPORT_2025.md) - Complete 2025 expansion

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Ways to Contribute
- Add high-quality repositories to `repositories.yaml`
- Improve search algorithms
- Add new MCP tools
- Enhance documentation
- Report bugs or request features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) for enabling AI-assistant integrations
- All the amazing open-source projects indexed in our knowledge base
- The GitHub API for making documentation discovery possible

## 📬 Contact

For questions, suggestions, or collaboration opportunities:
- Open an issue on GitHub
- Submit a pull request
- Star the repository to show support!

---

Built with ❤️ for developers who want their AI assistants to know everything!
