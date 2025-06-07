#!/usr/bin/env python3
"""
GitHub API client for fetching repository data and documentation
"""

import os
import asyncio
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import httpx
from pathlib import Path


class GitHubClient:
    """Async GitHub API client with rate limit handling"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "UnifiedDocsHub/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5)
        )
        
        self.rate_limit_remaining = 60  # Default for unauthenticated
        self.rate_limit_reset = None
    
    async def check_rate_limit(self):
        """Check current rate limit status"""
        response = await self.client.get("https://api.github.com/rate_limit")
        if response.status_code == 200:
            data = response.json()
            core = data['rate']
            self.rate_limit_remaining = core['remaining']
            self.rate_limit_reset = datetime.fromtimestamp(core['reset'])
            return core
        return None
    
    async def get_rate_limit(self) -> Dict:
        """Get current rate limit information for display"""
        rate_info = await self.check_rate_limit()
        if rate_info:
            return {
                'remaining': rate_info['remaining'],
                'limit': rate_info['limit'],
                'reset_time': datetime.fromtimestamp(rate_info['reset']).strftime('%Y-%m-%d %H:%M:%S')
            }
        return {
            'remaining': self.rate_limit_remaining,
            'limit': 60,
            'reset_time': 'Unknown'
        }
    
    async def wait_for_rate_limit(self):
        """Wait if rate limit is exhausted"""
        if self.rate_limit_remaining <= 1:
            if self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
                if wait_time > 0:
                    print(f"Rate limit exhausted. Waiting {wait_time:.0f} seconds...")
                    await asyncio.sleep(wait_time + 1)
    
    async def search_repositories(self, min_stars: int, max_results: int = 100) -> List[Dict]:
        """Search for popular repositories by star count"""
        repositories = []
        page = 1
        per_page = 100
        
        while len(repositories) < max_results:
            await self.wait_for_rate_limit()
            
            query = f"stars:>={min_stars}"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page
            }
            
            response = await self.client.get(
                "https://api.github.com/search/repositories",
                params=params
            )
            
            self.update_rate_limit_from_headers(response.headers)
            
            if response.status_code != 200:
                print(f"GitHub API error: {response.status_code}")
                break
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
            
            for repo in items:
                if len(repositories) >= max_results:
                    break
                
                repositories.append({
                    'owner': repo['owner']['login'],
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'stars': repo['stargazers_count'],
                    'language': repo.get('language'),
                    'description': repo.get('description', ''),
                    'default_branch': repo.get('default_branch', 'main')
                })
            
            page += 1
            
            # GitHub search API limits to 1000 results
            if len(repositories) >= 1000:
                break
        
        return repositories[:max_results]
    
    async def get_repository_info(self, owner: str, name: str) -> Optional[Dict]:
        """Get detailed repository information"""
        await self.wait_for_rate_limit()
        
        response = await self.client.get(
            f"https://api.github.com/repos/{owner}/{name}"
        )
        
        self.update_rate_limit_from_headers(response.headers)
        
        if response.status_code == 200:
            return response.json()
        return None
    
    async def fetch_file_content(self, owner: str, name: str, path: str, 
                                branch: str = "main") -> Optional[str]:
        """Fetch raw file content from GitHub"""
        # Try multiple common branches if the default fails
        branches_to_try = [branch, "main", "master"]
        
        for current_branch in branches_to_try:
            url = f"https://raw.githubusercontent.com/{owner}/{name}/{current_branch}/{path}"
            
            try:
                response = await self.client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    return response.text
            except Exception:
                continue
        
        return None
    
    async def discover_documentation_files(self, owner: str, name: str, 
                                         branch: str = "main") -> List[str]:
        """Discover documentation files in a repository"""
        doc_patterns = [
            "README.md", "readme.md", "README.rst", "README.txt",
            "CONTRIBUTING.md", "ARCHITECTURE.md", "DESIGN.md",
            "docs/", "documentation/", "doc/", "wiki/"
        ]
        
        found_files = []
        
        # First, try to get the repository tree
        await self.wait_for_rate_limit()
        
        response = await self.client.get(
            f"https://api.github.com/repos/{owner}/{name}/git/trees/{branch}",
            params={"recursive": 1}
        )
        
        self.update_rate_limit_from_headers(response.headers)
        
        if response.status_code == 200:
            tree = response.json()
            
            for item in tree.get('tree', []):
                path = item['path']
                
                # Check if it matches documentation patterns
                if any(pattern in path.lower() for pattern in ['readme', 'doc', 'contributing', 'guide', 'tutorial']):
                    if item['type'] == 'blob' and path.lower().endswith(('.md', '.rst', '.txt')):
                        found_files.append(path)
        else:
            # Fallback to checking known paths
            for pattern in doc_patterns:
                if not pattern.endswith('/'):
                    content = await self.fetch_file_content(owner, name, pattern, branch)
                    if content:
                        found_files.append(pattern)
        
        return found_files[:20]  # Limit to 20 files per repo
    
    def update_rate_limit_from_headers(self, headers: Dict):
        """Update rate limit info from response headers"""
        if 'x-ratelimit-remaining' in headers:
            self.rate_limit_remaining = int(headers['x-ratelimit-remaining'])
        if 'x-ratelimit-reset' in headers:
            self.rate_limit_reset = datetime.fromtimestamp(int(headers['x-ratelimit-reset']))
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for change detection"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
