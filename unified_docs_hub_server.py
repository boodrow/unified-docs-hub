#!/usr/bin/env python3
"""
Unified Documentation Hub MCP Server

Combines curated high-quality documentation sources with automatic discovery
of popular GitHub repositories. Provides intelligent search, deduplication,
and continuous learning capabilities.
"""

import asyncio
import json
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from fastmcp import FastMCP
from database import UnifiedDocsDatabase
from github_client import GitHubClient
from response_limiter import ResponseLimiter

# Initialize the MCP server
mcp = FastMCP("unified-docs-hub")

# Configuration
DB_PATH = Path(__file__).parent / "unified_docs.db"
REPOS_CONFIG = Path(__file__).parent / "repositories.yaml"
CACHE_HOURS = 168  # 7 days

# Global instances
db: UnifiedDocsDatabase = None
github_client: GitHubClient = None
config: Dict = None


async def initialize():
    """Initialize the server components"""
    global db, github_client, config
    
    # Initialize database
    db = UnifiedDocsDatabase(DB_PATH)
    
    # Initialize GitHub client
    github_client = GitHubClient()
    
    # Load configuration
    if REPOS_CONFIG.exists():
        with open(REPOS_CONFIG, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {'curated_repositories': [], 'discovery': {'enabled': True}}
    
    # Import curated repositories
    await import_curated_repositories()


async def import_curated_repositories():
    """Import curated repositories from configuration"""
    curated_repos = config.get('curated_repositories', [])
    
    for repo_config in curated_repos:
        # Parse repository name
        parts = repo_config['repo'].split('/')
        if len(parts) != 2:
            continue
        
        owner, name = parts
        
        repo_data = {
            'owner': owner,
            'name': name,
            'full_name': repo_config['repo'],
            'category': repo_config.get('category'),
            'description': repo_config.get('description'),
            'source': 'curated',
            'quality_score': repo_config.get('quality_score', 8),
            'priority': repo_config.get('priority', 'medium'),
            'doc_paths': repo_config.get('doc_paths', []),
            'topics': repo_config.get('topics', [])
        }
        
        # Get current star count from GitHub
        repo_info = await github_client.get_repository_info(owner, name)
        if repo_info:
            repo_data['stars'] = repo_info.get('stargazers_count', 0)
            repo_data['language'] = repo_info.get('language')
        
        db.upsert_repository(repo_data)


@mcp.tool()
async def unified_search(
    query: str,
    min_stars: Optional[int] = None,
    category: Optional[str] = None,
    source: Optional[str] = None
) -> str:
    """
    Search across all indexed documentation with intelligent filtering.
    
    Args:
        query: Search query (supports phrases, operators, wildcards)
        min_stars: Minimum star count filter
        category: Category filter like "AI/ML", "Web Development"
        source: Filter by "curated" or "discovered"
    
    Returns:
        Search results with snippets
    """
    await initialize()
    
    filters = {}
    if min_stars is not None:
        filters['min_stars'] = min_stars
    if category is not None:
        filters['category'] = category
    if source is not None:
        filters['source'] = source
    
    results = db.search_documents(query, filters if filters else None)
    return ResponseLimiter.format_search_response(results, query)


@mcp.tool()
async def index_repositories(
    mode: str = "smart",
    min_stars: int = 10000,
    count: int = 50
) -> str:
    """
    Index documentation from repositories using various strategies.
    
    Modes:
    - "smart": Index curated repos + discover new popular ones (recommended)
    - "curated": Only index curated repositories from config
    - "discover": Only discover and index new popular repositories
    - "update": Update existing indexed repositories
    
    Args:
        mode: Indexing mode (smart, curated, discover, update)
        min_stars: Minimum stars for discovery mode
        count: Number of repos to discover
    
    Returns:
        Indexing status report
    """
    output = [f"🔄 Indexing Documentation (Mode: {mode})\n"]
    
    indexed_count = 0
    error_count = 0
    
    if mode in ["smart", "curated"]:
        # Index curated repositories
        output.append("📚 Indexing curated repositories...")
        await import_curated_repositories()
        
        curated_repos = db.list_repositories({'source': 'curated'})
        for repo in curated_repos:
            try:
                await index_repository(repo)
                indexed_count += 1
                output.append(f"  ✓ {repo['full_name']}")
            except Exception as e:
                error_count += 1
                output.append(f"  ✗ {repo['full_name']}: {str(e)}")
    
    if mode in ["smart", "discover"]:
        # Discover new repositories
        output.append(f"\n🔍 Discovering popular repositories (≥{min_stars} stars)...")
        
        discovered = await github_client.search_repositories(min_stars, count)
        
        # Filter out already indexed repos
        existing = {r['full_name'] for r in db.list_repositories()}
        new_repos = [r for r in discovered if r['full_name'] not in existing]
        
        output.append(f"Found {len(new_repos)} new repositories")
        
        for repo_data in new_repos[:count]:
            repo_data['source'] = 'discovered'
            repo_id = db.upsert_repository(repo_data)
            
            try:
                repo_data['id'] = repo_id
                await index_repository(repo_data)
                indexed_count += 1
                output.append(f"  ✓ {repo_data['full_name']} ({repo_data['stars']:,} ⭐)")
            except Exception as e:
                error_count += 1
                output.append(f"  ✗ {repo_data['full_name']}: {str(e)}")
    
    if mode == "update":
        # Update existing repositories
        output.append("🔄 Updating existing repositories...")
        
        repos = db.list_repositories()
        for repo in repos:
            # Check if needs update (older than cache hours)
            if repo.get('last_indexed'):
                last_indexed = datetime.fromisoformat(repo['last_indexed'])
                if datetime.now() - last_indexed < timedelta(hours=CACHE_HOURS):
                    continue
            
            try:
                await index_repository(repo)
                indexed_count += 1
                output.append(f"  ✓ Updated {repo['full_name']}")
            except Exception as e:
                error_count += 1
                output.append(f"  ✗ Failed to update {repo['full_name']}: {str(e)}")
    
    # Summary
    output.append(f"\n📊 Indexing Summary:")
    output.append(f"  • Indexed: {indexed_count} repositories")
    output.append(f"  • Errors: {error_count}")
    
    # Get current statistics
    stats = db.get_statistics()
    output.append(f"\n📈 Database Statistics:")
    output.append(f"  • Total repositories: {stats['total_repositories']}")
    output.append(f"  • Curated: {stats['by_source']['curated']}")
    output.append(f"  • Discovered: {stats['by_source']['discovered']}")
    output.append(f"  • Total documents: {stats['total_documents']}")
    
    # Return as plain text with size limit
    result = '\n'.join(output)
    if len(result) > 50000:
        result = result[:49000] + "\n\n[Output truncated]"
    return result


async def index_repository(repo_data: Dict):
    """Index documentation files from a repository"""
    owner = repo_data['owner']
    name = repo_data['name']
    
    # Use curated doc paths if available, otherwise discover
    if repo_data['source'] == 'curated' and repo_data.get('doc_paths'):
        doc_files = repo_data['doc_paths']
    else:
        # Discover documentation files
        doc_files = await github_client.discover_documentation_files(
            owner, name, repo_data.get('default_branch', 'main')
        )
    
    if not doc_files:
        raise ValueError("No documentation files found")
    
    # Fetch and index each file
    docs_indexed = 0
    for file_path in doc_files:
        content = await github_client.fetch_file_content(
            owner, name, file_path, repo_data.get('default_branch', 'main')
        )
        
        if content:
            content_hash = github_client.calculate_content_hash(content)
            
            # Get repo_id if not provided
            if 'id' not in repo_data:
                db_repo = db.get_repository(repo_data['full_name'])
                if db_repo:
                    repo_data['id'] = db_repo['id']
            
            db.add_document(repo_data['id'], file_path, content, content_hash)
            docs_indexed += 1
    
    # Update last indexed timestamp
    db.conn.execute(
        "UPDATE repositories SET last_indexed = CURRENT_TIMESTAMP WHERE id = ?",
        (repo_data['id'],)
    )
    db.conn.commit()
    
    return docs_indexed


@mcp.tool()
async def list_repositories(
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    List indexed repositories with filtering options.
    
    Args:
        category: Filter by category (e.g., "AI/ML", "Web Development")
        source: Filter by source ("curated" or "discovered")
        limit: Maximum number of results
    
    Returns:
        Formatted list of repositories
    """
    filters = {}
    if category:
        filters['category'] = category
    if source:
        filters['source'] = source
    
    repos = db.list_repositories(filters)[:limit]
    
    title = "📚 Indexed Repositories"
    if category:
        title += f" - Category: {category}"
    if source:
        title += f" - Source: {source}"
    
    return ResponseLimiter.format_list_response(repos, title)


@mcp.tool()
async def get_repository_docs(repo_name: str) -> str:
    """
    Get all indexed documentation for a specific repository.
    
    Args:
        repo_name: Repository name in format "owner/repo"
    
    Returns:
        All documentation for the repository
    """
    await initialize()
    
    docs = db.get_repository_documents(repo_name)
    return ResponseLimiter.format_docs_response(docs, repo_name)


@mcp.tool()
async def get_statistics() -> str:
    """
    Get comprehensive statistics about the documentation index.
    
    Returns:
        Index statistics and summary
    """
    await initialize()
    
    stats = db.get_statistics()
    
    output = ["📊 Unified Documentation Hub Statistics\n"]
    
    # General stats
    output.append(f"📚 Total Repositories: {stats['total_repositories']:,}")
    output.append(f"📄 Total Documents: {stats['total_documents']:,}")
    output.append(f"💾 Database Size: {stats['database_size_mb']:.1f} MB")
    
    # Source breakdown
    output.append(f"\n🔍 By Source:")
    for source, count in stats['by_source'].items():
        output.append(f"  • {source.title()}: {count:,}")
    
    # Category breakdown
    output.append(f"\n📁 By Category:")
    for category, count in stats['by_category'].items():
        output.append(f"  • {category}: {count:,}")
    
    # Language breakdown
    output.append(f"\n💻 By Language (Top 10):")
    lang_items = sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True)
    for lang, count in lang_items[:10]:
        output.append(f"  • {lang}: {count:,}")
    
    # GitHub API status
    if github_client:
        try:
            # Try to get rate limit info
            if hasattr(github_client, 'get_rate_limit'):
                rate_limit = await github_client.get_rate_limit()
                output.append(f"\n🌐 GitHub API Status:")
                output.append(f"  • Remaining: {rate_limit['remaining']:,}/{rate_limit['limit']:,}")
                output.append(f"  • Resets: {rate_limit['reset_time']}")
            else:
                # Fallback for older github_client without get_rate_limit
                output.append(f"\n🌐 GitHub API Status:")
                output.append(f"  • Remaining: {github_client.rate_limit_remaining}")
                output.append(f"  • Rate limit info requires server restart")
        except Exception as e:
            output.append(f"\n🌐 GitHub API Status: Error - {str(e)}")
    
    return '\n'.join(output)


@mcp.tool()
async def list_categories() -> str:
    """
    List all available documentation categories with statistics.
    
    Returns:
        Categories and counts
    """
    await initialize()
    
    categories = db.get_categories()
    
    output = ["📁 Documentation Categories\n"]
    
    for cat in categories:
        output.append(f"• {cat['category']} ({cat['count']} repos)")
        if cat['example_repos']:
            examples = cat['example_repos'][:3]
            output.append(f"  Examples: {', '.join(examples)}")
    
    return '\n'.join(output)


@mcp.tool()
async def rebuild_search_index() -> str:
    """
    Rebuild the full-text search index.
    
    Use this when search is not working properly or returns SQL errors.
    This will recreate the FTS index from all existing documents.
    
    Returns:
        Status message
    """
    await initialize()
    
    try:
        count = db.rebuild_fts_index()
        return f"✅ Successfully rebuilt search index with {count} documents"
    except Exception as e:
        return f"❌ Failed to rebuild search index: {str(e)}"


if __name__ == "__main__":
    # Run as stdio MCP server
    asyncio.run(mcp.run())
