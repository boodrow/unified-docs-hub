# Unified Documentation Hub MCP Server

A powerful MCP server that unifies documentation from curated high-quality repositories and auto-discovered popular GitHub projects into a single, searchable knowledge base.

## 🌟 Key Features

- **Dual-Source Intelligence**: Combines curated repositories with auto-discovered popular projects
- **Intelligent Deduplication**: Prevents duplicate entries while preserving source metadata
- **Full-Text Search**: Lightning-fast search using SQLite FTS5 with snippet extraction
- **Quality Scoring**: Curated repos include quality scores and priority levels
- **Response Size Limiting**: Prevents HTTP2 GOAWAY errors with intelligent truncation
- **Continuous Learning**: Always discovering and indexing new documentation
- **Category Organization**: Browse documentation by technology categories
- **Real-Time Monitoring**: Dedicated dashboard for tracking indexing progress

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
cd /Users/buddewayne/Python Projects/MCP_Servers/documentation-mcp-server/unified-docs-hub
```

2. Set up Python environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run migration to import existing data:
```bash
./venv/bin/python migrate_existing_data.py
```

4. Add to your MCP configuration (`~/.codeium/windsurf/mcp_config.json`):
```json
{
  "unified-docs-hub": {
    "command": "/path/to/unified-docs-hub/venv/bin/python",
    "args": ["/path/to/unified-docs-hub/unified_docs_hub_server.py"],
    "env": {
      "GITHUB_TOKEN": "your-github-token"
    }
  }
}
```

5. Restart Windsurf to load the server

## 📋 MCP Tools

### `unified_search`
Search across all indexed documentation with intelligent filtering.

**Parameters:**
- `query` (required): Search query supporting phrases, operators, wildcards
- `min_stars` (optional): Minimum star count filter
- `category` (optional): Filter by category (e.g., "AI/ML", "Web Development")
- `source` (optional): Filter by "curated" or "discovered"

**Example:**
```
unified_search(query="transformer architecture", category="AI/ML", min_stars=1000)
```

### `index_repositories`
Index documentation from repositories using various strategies.

**Parameters:**
- `mode`: Indexing mode
  - `"smart"`: Index curated repos + discover new popular ones (recommended)
  - `"curated"`: Only index curated repositories from config
  - `"discover"`: Only discover and index new popular repositories
  - `"update"`: Update existing indexed repositories
- `min_stars` (optional): Minimum stars for discovery mode (default: 10000)
- `count` (optional): Number of repos to discover (default: 50)

**Example:**
```
index_repositories(mode="smart")
```

### `list_repositories`
List indexed repositories with filtering options.

**Parameters:**
- `category` (optional): Filter by category
- `source` (optional): Filter by source ("curated" or "discovered")
- `limit` (optional): Maximum number of results (default: 50)

### `get_repository_docs`
Get all indexed documentation for a specific repository.

**Parameters:**
- `repo_name` (required): Repository name in format "owner/repo"

### `get_statistics`
Get comprehensive statistics about the documentation index.

Returns database size, repository counts, category breakdown, and GitHub API status.

### `list_categories`
List all available documentation categories with statistics.

## 📊 Monitoring

### Real-Time Dashboard
Monitor the unified docs hub progress:
```bash
./unified-dashboard.sh
```

Features:
- Server status (running/stopped, CPU, memory)
- Database statistics and size
- Progress bars for indexing targets
- Top categories and repositories
- Recently indexed repos with timestamps

### Main MCP Dashboard
View all MCP servers including unified docs hub:
```bash
./mcp-dashboard-final.sh
```

## 🏗️ Architecture

### Core Components

1. **Database Module** (`database.py`)
   - SQLite with FTS5 for full-text search
   - Efficient indexing and retrieval
   - Deduplication logic

2. **GitHub Client** (`github_client.py`)
   - Async API integration
   - Rate limit handling
   - Documentation discovery

3. **Response Limiter** (`response_limiter.py`)
   - Prevents protocol errors
   - Intelligent content truncation
   - Maintains response quality

4. **MCP Server** (`unified_docs_hub_server.py`)
   - FastMCP implementation
   - Async request handling
   - Tool orchestration

### Database Schema

```sql
-- Repositories table
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    full_name TEXT UNIQUE,
    stars INTEGER,
    language TEXT,
    source TEXT,  -- 'curated' or 'discovered'
    category TEXT,
    quality_score INTEGER,  -- 1-10 for curated
    priority TEXT,  -- high/medium/low
    last_indexed TIMESTAMP
);

-- Documents table with FTS5
CREATE VIRTUAL TABLE documents USING fts5(
    repo_id,
    path,
    content,
    content_hash,
    indexed_at
);
```

## 🔧 Configuration

### repositories.yaml
Define curated repositories with metadata:
```yaml
repositories:
  - full_name: "facebook/react"
    category: "Web Development"
    quality_score: 10
    priority: "high"
    doc_paths:
      - "docs/"
      - "README.md"
```

### Environment Variables
- `GITHUB_TOKEN`: GitHub personal access token for API requests (recommended)

## 🎯 Usage Strategies

### Initial Setup
1. Run `index_repositories(mode="smart")` to populate with curated + popular repos
2. Use `get_statistics()` to verify indexing success
3. Test with `unified_search(query="your topic")`

### Continuous Learning
1. Schedule weekly `index_repositories(mode="update")` to refresh docs
2. Monthly `index_repositories(mode="discover")` to find new repos
3. Monitor trending repos and add to curated list

### Search Tips
- Use quotes for exact phrases: `"react hooks"`
- Combine filters for precision: `category="AI/ML" AND min_stars=5000`
- Explore categories first with `list_categories()`

## ⚡ Performance

- Response size limited to prevent protocol errors
- Async operations for efficient API usage
- FTS5 provides sub-second search results
- Incremental indexing minimizes API calls
- Database typically under 100MB for thousands of docs

## 🐛 Troubleshooting

### Server won't start
- Check Python version (3.13+ recommended)
- Verify all dependencies installed
- Ensure database path is writable

### No search results
- Run `get_statistics()` to check if repos are indexed
- Try broader search terms
- Check category filters

### HTTP2 GOAWAY errors
- Already handled by response limiter
- If persists, reduce result limits

### GitHub API rate limits
- Add GITHUB_TOKEN to environment
- Use "update" mode instead of full reindex
- Check rate limit with `get_statistics()`

## 🚀 Future Enhancements

1. **Semantic Search**: Vector embeddings for concept-based search
2. **Code Examples**: Extract and index code snippets
3. **Multi-Language**: Support for non-English documentation
4. **Incremental Sync**: Real-time updates via webhooks
5. **Export/Import**: Share indexes between instances
6. **Analytics**: Usage patterns and popular searches

## 📄 License

This project is part of the MCP ecosystem and follows the same licensing terms as the Windsurf MCP implementation.
