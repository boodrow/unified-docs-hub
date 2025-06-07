"""
Response size limiter for MCP servers to prevent HTTP2 GOAWAY errors.
"""

import json
from typing import List, Dict, Any, Optional


class ResponseLimiter:
    """Limits MCP response sizes to prevent protocol errors"""
    
    # Maximum response size in bytes (500KB to be safe)
    MAX_RESPONSE_SIZE = 500 * 1024
    
    # Maximum content preview per document
    MAX_CONTENT_PREVIEW = 1000
    
    # Maximum number of search results
    MAX_SEARCH_RESULTS = 20
    
    @staticmethod
    def truncate_text(text: str, max_length: int) -> str:
        """Truncate text with ellipsis if needed"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 4] + " ..."
    
    @staticmethod
    def estimate_size(obj: Any) -> int:
        """Estimate the size of an object when serialized"""
        try:
            return len(json.dumps(obj))
        except:
            return len(str(obj))
    
    @classmethod
    def limit_search_results(cls, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Limit search results to prevent large responses"""
        limited_results = []
        total_size = 0
        
        for result in results[:cls.MAX_SEARCH_RESULTS]:
            # Truncate snippet
            if 'snippet' in result:
                result['snippet'] = cls.truncate_text(
                    result['snippet'], 
                    200  # Short snippets
                )
            
            # Truncate description
            if 'description' in result:
                result['description'] = cls.truncate_text(
                    result['description'], 
                    100
                )
            
            # Check cumulative size
            result_size = cls.estimate_size(result)
            if total_size + result_size > cls.MAX_RESPONSE_SIZE * 0.8:
                break
            
            limited_results.append(result)
            total_size += result_size
        
        return limited_results
    
    @classmethod
    def limit_document_content(cls, content: str) -> str:
        """Limit document content preview"""
        return cls.truncate_text(content, cls.MAX_CONTENT_PREVIEW)
    
    @classmethod
    def format_search_response(cls, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results with size limits"""
        if not results:
            return f"No results found for '{query}'"
        
        limited_results = cls.limit_search_results(results)
        
        output = [f"🔍 Search Results for '{query}'"]
        output.append(f"Showing {len(limited_results)} of {len(results)} results\n")
        
        for r in limited_results:
            output.append(f"📦 {r.get('full_name', 'Unknown')} ⭐ {r.get('stars', 0):,}")
            
            if r.get('language'):
                output.append(f"   Language: {r['language']}")
            
            if r.get('path'):
                output.append(f"   File: {r['path']}")
            
            if r.get('snippet'):
                output.append(f"   Preview: {r['snippet']}")
            
            output.append("")  # Empty line between results
        
        result_text = '\n'.join(output)
        
        # Final size check
        if len(result_text) > cls.MAX_RESPONSE_SIZE:
            return result_text[:cls.MAX_RESPONSE_SIZE - 100] + "\n\n[Response truncated due to size limits]"
        
        return result_text
    
    @classmethod
    def format_docs_response(cls, docs: List[Dict[str, Any]], repo_name: str) -> str:
        """Format documentation response with size limits"""
        if not docs:
            return f"No documentation found for '{repo_name}'"
        
        output = [f"📚 Documentation for {repo_name}\n"]
        total_size = len(output[0])
        
        for i, doc in enumerate(docs):
            section = []
            section.append(f"{'='*50}")
            section.append(f"📄 {doc.get('path', 'Unknown')}")
            section.append(f"{'='*50}")
            
            content = cls.limit_document_content(doc.get('content', ''))
            section.append(content)
            
            if doc.get('content', '') and len(doc['content']) > cls.MAX_CONTENT_PREVIEW:
                section.append("\n[Content truncated - use specific file tools to view full content]")
            
            section.append("")
            
            section_text = '\n'.join(section)
            section_size = len(section_text)
            
            # Check if adding this section would exceed limits
            if total_size + section_size > cls.MAX_RESPONSE_SIZE * 0.9:
                output.append(f"\n[{len(docs) - i} more documents not shown due to size limits]")
                break
            
            output.extend(section)
            total_size += section_size
        
        return '\n'.join(output)
    
    @classmethod
    def format_list_response(cls, items: List[Dict[str, Any]], title: str) -> str:
        """Format list responses with size limits"""
        output = [title + "\n"]
        
        for item in items[:50]:  # Limit to 50 items
            line = f"• {item.get('name', 'Unknown')}"
            
            if item.get('stars'):
                line += f" ⭐ {item['stars']:,}"
            
            if item.get('category'):
                line += f" [{item['category']}]"
            
            if item.get('description'):
                desc = cls.truncate_text(item['description'], 60)
                line += f" - {desc}"
            
            output.append(line)
        
        if len(items) > 50:
            output.append(f"\n... and {len(items) - 50} more")
        
        return '\n'.join(output)
