"""
Extended format handlers for various documentation formats
Supports: Markdown, MDX, reStructuredText, AsciiDoc, Jupyter Notebooks
"""

import re
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml

class FormatHandler(ABC):
    """Base class for format handlers"""
    
    @staticmethod
    @abstractmethod
    def can_handle(file_path: str) -> bool:
        """Check if this handler can process the given file"""
        pass
        
    @staticmethod
    @abstractmethod
    def extract_content(content: str) -> Dict[str, Any]:
        """Extract structured content from the file"""
        pass
        
    @staticmethod
    @abstractmethod
    def to_markdown(content: str) -> str:
        """Convert content to markdown format"""
        pass


class MarkdownHandler(FormatHandler):
    """Handler for standard Markdown files"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return file_path.lower().endswith(('.md', '.markdown'))
        
    @staticmethod
    def extract_content(content: str) -> Dict[str, Any]:
        # Extract frontmatter if present
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    content = parts[2]
                except:
                    pass
                    
        # Extract headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
        
        return {
            'frontmatter': frontmatter,
            'headers': [(len(h[0]), h[1]) for h in headers],
            'code_blocks': [{'language': cb[0], 'code': cb[1]} for cb in code_blocks],
            'content': content,
            'format': 'markdown'
        }
        
    @staticmethod
    def to_markdown(content: str) -> str:
        # Already markdown
        return content


class MDXHandler(FormatHandler):
    """Handler for MDX (Markdown with JSX) files"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return file_path.lower().endswith('.mdx')
        
    @staticmethod
    def extract_content(content: str) -> Dict[str, Any]:
        # Extract imports
        imports = re.findall(r'^import\s+.*$', content, re.MULTILINE)
        
        # Extract JSX components
        jsx_components = re.findall(r'<(\w+)[^>]*>', content)
        
        # Remove JSX for markdown extraction
        cleaned_content = re.sub(r'<[^>]+>', '', content)
        
        # Use markdown handler for the rest
        md_data = MarkdownHandler.extract_content(cleaned_content)
        
        return {
            **md_data,
            'imports': imports,
            'jsx_components': list(set(jsx_components)),
            'format': 'mdx'
        }
        
    @staticmethod
    def to_markdown(content: str) -> str:
        # Remove imports
        content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)
        
        # Convert JSX components to markdown equivalents where possible
        # Simple component to markdown conversions
        conversions = {
            r'<Callout[^>]*>(.*?)</Callout>': r'> **Note:** \1',
            r'<Warning[^>]*>(.*?)</Warning>': r'> **Warning:** \1',
            r'<Info[^>]*>(.*?)</Info>': r'> **Info:** \1',
            r'<CodeBlock[^>]*>(.*?)</CodeBlock>': r'```\n\1\n```',
        }
        
        for pattern, replacement in conversions.items():
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
        # Remove remaining JSX
        content = re.sub(r'<[^>]+>', '', content)
        
        return content.strip()


class ReStructuredTextHandler(FormatHandler):
    """Handler for reStructuredText files"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return file_path.lower().endswith('.rst')
        
    @staticmethod
    def extract_content(content: str) -> Dict[str, Any]:
        # Extract headers (underlined with =, -, ~, etc.)
        headers = []
        lines = content.split('\n')
        for i in range(len(lines) - 1):
            if lines[i] and lines[i+1] and all(c in '=-~^"' for c in lines[i+1].strip()):
                if len(lines[i+1].strip()) >= len(lines[i].strip()):
                    headers.append(lines[i].strip())
                    
        # Extract code blocks
        code_blocks = re.findall(r'::\s*(\w*)\n\n((?:    .*\n)*)', content)
        
        # Extract directives
        directives = re.findall(r'^\.\. (\w+)::', content, re.MULTILINE)
        
        return {
            'headers': headers,
            'code_blocks': [{'language': cb[0], 'code': cb[1].strip()} for cb in code_blocks],
            'directives': directives,
            'content': content,
            'format': 'rst'
        }
        
    @staticmethod
    def to_markdown(content: str) -> str:
        # Convert headers
        lines = content.split('\n')
        markdown_lines = []
        i = 0
        
        while i < len(lines):
            if i < len(lines) - 1 and lines[i] and lines[i+1]:
                if all(c == '=' for c in lines[i+1].strip()) and len(lines[i+1].strip()) >= len(lines[i].strip()):
                    markdown_lines.append(f"# {lines[i]}")
                    i += 2
                    continue
                elif all(c == '-' for c in lines[i+1].strip()) and len(lines[i+1].strip()) >= len(lines[i].strip()):
                    markdown_lines.append(f"## {lines[i]}")
                    i += 2
                    continue
                elif all(c == '~' for c in lines[i+1].strip()) and len(lines[i+1].strip()) >= len(lines[i].strip()):
                    markdown_lines.append(f"### {lines[i]}")
                    i += 2
                    continue
                    
            markdown_lines.append(lines[i])
            i += 1
            
        content = '\n'.join(markdown_lines)
        
        # Convert code blocks
        content = re.sub(r'::\s*(\w*)\n\n((?:    .*\n)*)', 
                        lambda m: f"```{m.group(1)}\n{m.group(2).strip()}\n```", 
                        content)
        
        # Convert links
        content = re.sub(r'`([^<]+) <([^>]+)>`_', r'[\1](\2)', content)
        
        # Convert emphasis
        content = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', content)
        content = re.sub(r'\*([^*]+)\*', r'*\1*', content)
        
        return content


class AsciiDocHandler(FormatHandler):
    """Handler for AsciiDoc files"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return file_path.lower().endswith(('.adoc', '.asciidoc'))
        
    @staticmethod
    def extract_content(content: str) -> Dict[str, Any]:
        # Extract headers
        headers = re.findall(r'^(=+)\s+(.+)$', content, re.MULTILINE)
        
        # Extract code blocks
        code_blocks = []
        # Source blocks
        source_blocks = re.findall(r'\[source,(\w+)\]\n----\n(.*?)\n----', content, re.DOTALL)
        code_blocks.extend([{'language': sb[0], 'code': sb[1]} for sb in source_blocks])
        
        # Simple code blocks
        simple_blocks = re.findall(r'----\n(.*?)\n----', content, re.DOTALL)
        code_blocks.extend([{'language': '', 'code': sb} for sb in simple_blocks])
        
        # Extract attributes
        attributes = {}
        attr_matches = re.findall(r'^:(\w+):\s*(.*)$', content, re.MULTILINE)
        for attr, value in attr_matches:
            attributes[attr] = value
            
        return {
            'headers': [(len(h[0]), h[1]) for h in headers],
            'code_blocks': code_blocks,
            'attributes': attributes,
            'content': content,
            'format': 'asciidoc'
        }
        
    @staticmethod
    def to_markdown(content: str) -> str:
        # Convert headers
        content = re.sub(r'^(=+)\s+(.+)$', 
                        lambda m: '#' * len(m.group(1)) + ' ' + m.group(2), 
                        content, flags=re.MULTILINE)
        
        # Convert source blocks
        content = re.sub(r'\[source,(\w+)\]\n----\n(.*?)\n----', 
                        r'```\1\n\2\n```', 
                        content, flags=re.DOTALL)
        
        # Convert simple code blocks
        content = re.sub(r'----\n(.*?)\n----', r'```\n\1\n```', content, flags=re.DOTALL)
        
        # Convert links
        content = re.sub(r'link:([^\[]+)\[([^\]]+)\]', r'[\2](\1)', content)
        
        # Convert emphasis
        content = re.sub(r'\*([^*]+)\*', r'**\1**', content)
        content = re.sub(r'_([^_]+)_', r'*\1*', content)
        
        # Remove attributes
        content = re.sub(r'^:(\w+):\s*(.*)$', '', content, flags=re.MULTILINE)
        
        return content.strip()


class JupyterNotebookHandler(FormatHandler):
    """Handler for Jupyter Notebook files"""
    
    @staticmethod
    def can_handle(file_path: str) -> bool:
        return file_path.lower().endswith('.ipynb')
        
    @staticmethod
    def extract_content(content: str) -> Dict[str, Any]:
        try:
            notebook = json.loads(content)
            
            cells = []
            headers = []
            code_blocks = []
            
            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type')
                source = ''.join(cell.get('source', []))
                
                if cell_type == 'markdown':
                    cells.append({'type': 'markdown', 'content': source})
                    # Extract headers from markdown cells
                    cell_headers = re.findall(r'^(#{1,6})\s+(.+)$', source, re.MULTILINE)
                    headers.extend([(len(h[0]), h[1]) for h in cell_headers])
                    
                elif cell_type == 'code':
                    cells.append({'type': 'code', 'content': source})
                    code_blocks.append({
                        'language': notebook.get('metadata', {}).get('language_info', {}).get('name', 'python'),
                        'code': source
                    })
                    
            return {
                'cells': cells,
                'headers': headers,
                'code_blocks': code_blocks,
                'metadata': notebook.get('metadata', {}),
                'format': 'jupyter'
            }
        except:
            return {
                'error': 'Failed to parse Jupyter notebook',
                'format': 'jupyter'
            }
            
    @staticmethod
    def to_markdown(content: str) -> str:
        try:
            notebook = json.loads(content)
            markdown_parts = []
            
            language = notebook.get('metadata', {}).get('language_info', {}).get('name', 'python')
            
            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type')
                source = ''.join(cell.get('source', []))
                
                if cell_type == 'markdown':
                    markdown_parts.append(source)
                elif cell_type == 'code' and source.strip():
                    markdown_parts.append(f"```{language}\n{source}\n```")
                    
                    # Include output if present and not too large
                    outputs = cell.get('outputs', [])
                    for output in outputs[:2]:  # Limit outputs
                        if output.get('output_type') == 'stream':
                            text = ''.join(output.get('text', []))
                            if text and len(text) < 500:
                                markdown_parts.append(f"Output:\n```\n{text}\n```")
                        elif output.get('output_type') == 'execute_result':
                            data = output.get('data', {})
                            if 'text/plain' in data:
                                text = ''.join(data['text/plain'])
                                if len(text) < 500:
                                    markdown_parts.append(f"Output:\n```\n{text}\n```")
                                    
            return '\n\n'.join(markdown_parts)
        except:
            return "Error: Could not parse Jupyter notebook"


class FormatHandlerRegistry:
    """Registry for all format handlers"""
    
    handlers = [
        MarkdownHandler,
        MDXHandler,
        ReStructuredTextHandler,
        AsciiDocHandler,
        JupyterNotebookHandler
    ]
    
    @classmethod
    def get_handler(cls, file_path: str) -> Optional[FormatHandler]:
        """Get appropriate handler for file"""
        for handler in cls.handlers:
            if handler.can_handle(file_path):
                return handler
        return None
        
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Check if file format is supported"""
        return any(handler.can_handle(file_path) for handler in cls.handlers)
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported file extensions"""
        extensions = []
        # Hardcoded for now, could be made dynamic
        extensions.extend(['.md', '.markdown'])
        extensions.append('.mdx')
        extensions.append('.rst')
        extensions.extend(['.adoc', '.asciidoc'])
        extensions.append('.ipynb')
        return extensions


# Testing
if __name__ == "__main__":
    # Test different formats
    test_files = {
        'test.md': '# Header\n\nSome **bold** text\n\n```python\nprint("hello")\n```',
        'test.mdx': 'import Component from "./component"\n\n# Header\n\n<Callout>Note text</Callout>',
        'test.rst': 'Header\n======\n\nSome text\n\n::\n\n    code block',
        'test.adoc': '= Header\n\nSome *bold* text\n\n[source,python]\n----\nprint("hello")\n----'
    }
    
    for filename, content in test_files.items():
        print(f"\n{filename}:")
        handler = FormatHandlerRegistry.get_handler(filename)
        if handler:
            data = handler.extract_content(content)
            print(f"  Format: {data.get('format')}")
            print(f"  Headers: {data.get('headers', [])}")
            print(f"  Code blocks: {len(data.get('code_blocks', []))}")
            
            markdown = handler.to_markdown(content)
            print(f"  Markdown preview: {markdown[:100]}...")
