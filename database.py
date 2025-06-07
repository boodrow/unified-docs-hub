#!/usr/bin/env python3
"""
Database schema and operations for Unified Docs Hub
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class UnifiedDocsDatabase:
    """Manages the SQLite database for unified documentation"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database with enhanced schema"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Enable FTS5
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Repository metadata table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                owner TEXT NOT NULL,
                name TEXT NOT NULL,
                full_name TEXT UNIQUE NOT NULL,
                stars INTEGER DEFAULT 0,
                language TEXT,
                category TEXT,
                description TEXT,
                source TEXT NOT NULL CHECK (source IN ('curated', 'discovered')),
                quality_score REAL DEFAULT 0.5,
                quality_grade TEXT DEFAULT 'C',
                quality_metrics TEXT,  -- JSON object with detailed scores
                priority TEXT DEFAULT 'medium',
                doc_paths TEXT,  -- JSON array
                topics TEXT,     -- JSON array
                last_indexed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner, name)
            )
        """)
        
        # Documents table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                repo_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                content TEXT,
                content_hash TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE,
                UNIQUE(repo_id, path)
            )
        """)
        
        # Full-text search table
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                repo_full_name,
                path,
                content
            )
        """)
        
        # Triggers to keep FTS in sync
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents
            BEGIN
                INSERT INTO documents_fts(repo_full_name, path, content)
                SELECT 
                    r.full_name,
                    new.path,
                    new.content
                FROM repositories r
                WHERE r.id = new.repo_id;
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents
            BEGIN
                UPDATE documents_fts 
                SET 
                    repo_full_name = (SELECT full_name FROM repositories WHERE id = new.repo_id),
                    path = new.path,
                    content = new.content
                WHERE rowid = new.id;
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents
            BEGIN
                DELETE FROM documents_fts WHERE rowid = old.id;
            END
        """)
        
        # Indexing history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS indexing_history (
                id INTEGER PRIMARY KEY,
                repo_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                documents_indexed INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_repos_source ON repositories(source)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_repos_category ON repositories(category)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_repos_stars ON repositories(stars DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_docs_repo ON documents(repo_id)")
        
        self.conn.commit()
    
    def upsert_repository(self, repo_data: Dict) -> int:
        """Insert or update repository metadata"""
        doc_paths = json.dumps(repo_data.get('doc_paths', []))
        topics = json.dumps(repo_data.get('topics', []))
        quality_metrics = json.dumps(repo_data.get('quality_metrics', {}))
        
        cursor = self.conn.execute("""
            INSERT INTO repositories (
                owner, name, full_name, stars, language, category,
                description, source, quality_score, quality_grade, quality_metrics, priority, doc_paths, topics
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(owner, name) DO UPDATE SET
                stars = excluded.stars,
                language = excluded.language,
                category = COALESCE(excluded.category, category),
                description = COALESCE(excluded.description, description),
                quality_score = excluded.quality_score,
                quality_grade = excluded.quality_grade,
                quality_metrics = excluded.quality_metrics,
                priority = excluded.priority,
                doc_paths = excluded.doc_paths,
                topics = excluded.topics
        """, (
            repo_data['owner'],
            repo_data['name'],
            repo_data['full_name'],
            repo_data.get('stars', 0),
            repo_data.get('language'),
            repo_data.get('category'),
            repo_data.get('description'),
            repo_data.get('source', 'discovered'),
            repo_data.get('quality_score', 0.5),
            repo_data.get('quality_grade', 'C'),
            quality_metrics,
            repo_data.get('priority', 'medium'),
            doc_paths,
            topics
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def add_document(self, repo_id: int, path: str, content: str, content_hash: str):
        """Add or update a document"""
        self.conn.execute("""
            INSERT INTO documents (repo_id, path, content, content_hash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(repo_id, path) DO UPDATE SET
                content = excluded.content,
                content_hash = excluded.content_hash,
                indexed_at = CURRENT_TIMESTAMP
        """, (repo_id, path, content, content_hash))
        self.conn.commit()
    
    def search_documents(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search documents with optional filters"""
        sql = """
            SELECT 
                r.full_name,
                r.stars,
                r.category,
                r.description,
                r.source,
                r.quality_score,
                documents_fts.path,
                snippet(documents_fts, 2, '<b>', '</b>', '...', 64) as snippet,
                rank
            FROM documents_fts
            JOIN documents d ON documents_fts.path = d.path
            JOIN repositories r ON documents_fts.repo_full_name = r.full_name
            WHERE documents_fts MATCH ?
        """
        
        params = [query]
        
        if filters:
            if filters.get('min_stars'):
                sql += " AND r.stars >= ?"
                params.append(filters['min_stars'])
            
            if filters.get('category'):
                sql += " AND r.category = ?"
                params.append(filters['category'])
            
            if filters.get('source'):
                sql += " AND r.source = ?"
                params.append(filters['source'])
        
        sql += " ORDER BY rank, r.quality_score DESC, r.stars DESC LIMIT 50"
        
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_repository(self, full_name: str) -> Optional[Dict]:
        """Get repository by full name"""
        cursor = self.conn.execute("""
            SELECT * FROM repositories WHERE full_name = ?
        """, (full_name,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data['doc_paths'] = json.loads(data['doc_paths']) if data['doc_paths'] else []
            data['topics'] = json.loads(data['topics']) if data['topics'] else []
            data['quality_metrics'] = json.loads(data['quality_metrics']) if data['quality_metrics'] else {}
            return data
        return None
    
    def list_repositories(self, filters: Optional[Dict] = None) -> List[Dict]:
        """List repositories with optional filters"""
        sql = "SELECT * FROM repositories WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('category'):
                sql += " AND category = ?"
                params.append(filters['category'])
            
            if filters.get('source'):
                sql += " AND source = ?"
                params.append(filters['source'])
            
            if filters.get('min_stars'):
                sql += " AND stars >= ?"
                params.append(filters['min_stars'])
        
        sql += " ORDER BY quality_score DESC, stars DESC"
        
        cursor = self.conn.execute(sql, params)
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data['doc_paths'] = json.loads(data['doc_paths']) if data['doc_paths'] else []
            data['topics'] = json.loads(data['topics']) if data['topics'] else []
            data['quality_metrics'] = json.loads(data['quality_metrics']) if data['quality_metrics'] else {}
            results.append(data)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Repository counts
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN source = 'curated' THEN 1 END) as curated,
                COUNT(CASE WHEN source = 'discovered' THEN 1 END) as discovered
            FROM repositories
        """)
        repo_stats = cursor.fetchone()
        stats['total_repositories'] = repo_stats['total']
        stats['by_source'] = {
            'curated': repo_stats['curated'],
            'discovered': repo_stats['discovered']
        }
        
        # Category breakdown
        cursor = self.conn.execute("""
            SELECT category, COUNT(*) as count
            FROM repositories
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Document count
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = cursor.fetchone()['count']
        
        # Top languages
        cursor = self.conn.execute("""
            SELECT language, COUNT(*) as count
            FROM repositories
            WHERE language IS NOT NULL
            GROUP BY language
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['by_language'] = {row['language']: row['count'] for row in cursor.fetchall()}
        
        # Database size in MB
        cursor = self.conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats['database_size_mb'] = cursor.fetchone()['size'] / (1024 * 1024)
        
        return stats
    
    def get_categories(self) -> List[Dict]:
        """Get all categories with repository counts and examples"""
        cursor = self.conn.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                GROUP_CONCAT(full_name, ', ') as example_repos
            FROM repositories
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            # Limit example repos to first 3
            if data['example_repos']:
                data['example_repos'] = data['example_repos'].split(', ')[:3]
            else:
                data['example_repos'] = []
            results.append(data)
        
        return results
    
    def get_repository_documents(self, repo_name: str) -> List[Dict]:
        """Get all documents for a specific repository"""
        cursor = self.conn.execute("""
            SELECT 
                d.path,
                d.content,
                d.indexed_at,
                r.full_name,
                r.category,
                r.stars
            FROM documents d
            JOIN repositories r ON d.repo_id = r.id
            WHERE r.full_name = ?
            ORDER BY d.path
        """, (repo_name,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def rebuild_fts_index(self):
        """Rebuild the FTS index from scratch"""
        # First, clear the existing FTS data
        self.conn.execute("DELETE FROM documents_fts")
        
        # Re-insert all documents into FTS
        cursor = self.conn.execute("""
            INSERT INTO documents_fts(repo_full_name, path, content)
            SELECT 
                r.full_name,
                d.path,
                d.content
            FROM documents d
            JOIN repositories r ON d.repo_id = r.id
        """)
        
        self.conn.commit()
        
        # Return count of indexed documents
        return cursor.rowcount
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
