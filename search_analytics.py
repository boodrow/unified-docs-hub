"""
Search analytics module for tracking and analyzing search patterns
"""

import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import json

class SearchAnalytics:
    def __init__(self, db_path: str = "unified_docs_analytics.db"):
        self.conn = sqlite3.connect(db_path)
        self.init_database()
        
    def init_database(self):
        """Initialize analytics database tables"""
        # Search queries log
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER DEFAULT 0,
                clicked_results TEXT,  -- JSON array of clicked result IDs
                search_time REAL,     -- Time taken for search in seconds
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Popular searches cache
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS popular_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE NOT NULL,
                search_count INTEGER DEFAULT 1,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                avg_results_count REAL DEFAULT 0,
                avg_search_time REAL DEFAULT 0
            )
        """)
        
        # Search categories tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS search_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                search_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Missing documentation tracking
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS missing_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                query TEXT NOT NULL,
                request_count INTEGER DEFAULT 1,
                first_requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        
    def log_search(self, query: str, results_count: int, search_time: float, 
                   clicked_results: List[str] = None):
        """Log a search query and its results"""
        # Log the individual search
        self.conn.execute("""
            INSERT INTO search_queries (query, results_count, clicked_results, search_time)
            VALUES (?, ?, ?, ?)
        """, (query, results_count, json.dumps(clicked_results or []), search_time))
        
        # Update popular searches
        cursor = self.conn.execute("""
            SELECT search_count, avg_results_count, avg_search_time 
            FROM popular_searches WHERE query = ?
        """, (query,))
        
        row = cursor.fetchone()
        if row:
            # Update existing entry
            count, avg_results, avg_time = row
            new_count = count + 1
            new_avg_results = (avg_results * count + results_count) / new_count
            new_avg_time = (avg_time * count + search_time) / new_count
            
            self.conn.execute("""
                UPDATE popular_searches 
                SET search_count = ?, avg_results_count = ?, avg_search_time = ?, 
                    last_searched = CURRENT_TIMESTAMP
                WHERE query = ?
            """, (new_count, new_avg_results, new_avg_time, query))
        else:
            # Insert new entry
            self.conn.execute("""
                INSERT INTO popular_searches (query, search_count, avg_results_count, avg_search_time)
                VALUES (?, 1, ?, ?)
            """, (query, results_count, search_time))
            
        # Track categories from query
        self._track_categories(query)
        
        # Track if no results found
        if results_count == 0:
            self._track_missing_docs(query)
            
        self.conn.commit()
        
    def _track_categories(self, query: str):
        """Extract and track categories from search query"""
        # Category keywords mapping
        category_keywords = {
            'AI/ML': ['ai', 'ml', 'machine learning', 'deep learning', 'neural', 'tensorflow', 'pytorch'],
            'Web Development': ['react', 'vue', 'angular', 'frontend', 'backend', 'web', 'javascript', 'css'],
            'Mobile Development': ['ios', 'android', 'mobile', 'react native', 'flutter', 'swift'],
            'Databases': ['sql', 'database', 'mongodb', 'postgresql', 'redis', 'mysql'],
            'Cloud/DevOps': ['docker', 'kubernetes', 'aws', 'azure', 'cloud', 'devops', 'ci/cd'],
            'Security': ['security', 'auth', 'encryption', 'owasp', 'vulnerability'],
            'Testing': ['test', 'testing', 'jest', 'pytest', 'unit test', 'e2e'],
            'API Development': ['api', 'rest', 'graphql', 'grpc', 'endpoint']
        }
        
        query_lower = query.lower()
        detected_categories = []
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_categories.append(category)
                
        # Update category counts
        for category in detected_categories:
            cursor = self.conn.execute("""
                SELECT search_count FROM search_categories WHERE category = ?
            """, (category,))
            
            row = cursor.fetchone()
            if row:
                self.conn.execute("""
                    UPDATE search_categories 
                    SET search_count = search_count + 1, last_updated = CURRENT_TIMESTAMP
                    WHERE category = ?
                """, (category,))
            else:
                self.conn.execute("""
                    INSERT INTO search_categories (category, search_count)
                    VALUES (?, 1)
                """, (category,))
                
    def _track_missing_docs(self, query: str):
        """Track queries with no results as missing documentation"""
        # Try to extract topic from query
        topic = self._extract_topic(query)
        
        cursor = self.conn.execute("""
            SELECT request_count FROM missing_docs 
            WHERE topic = ? AND query = ?
        """, (topic, query))
        
        row = cursor.fetchone()
        if row:
            self.conn.execute("""
                UPDATE missing_docs 
                SET request_count = request_count + 1, last_requested = CURRENT_TIMESTAMP
                WHERE topic = ? AND query = ?
            """, (topic, query))
        else:
            self.conn.execute("""
                INSERT INTO missing_docs (topic, query)
                VALUES (?, ?)
            """, (topic, query))
            
    def _extract_topic(self, query: str) -> str:
        """Extract main topic from query"""
        # Simple topic extraction - take first significant word
        stop_words = {'how', 'to', 'what', 'where', 'when', 'why', 'is', 'are', 'the', 'a', 'an'}
        words = query.lower().split()
        
        for word in words:
            if word not in stop_words and len(word) > 2:
                return word
                
        return query.split()[0] if query.split() else 'unknown'
        
    def get_popular_searches(self, limit: int = 20, days: int = 30) -> List[Dict]:
        """Get most popular searches in the last N days"""
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor = self.conn.execute("""
            SELECT query, search_count, avg_results_count, avg_search_time
            FROM popular_searches
            WHERE last_searched >= ?
            ORDER BY search_count DESC
            LIMIT ?
        """, (since_date, limit))
        
        return [
            {
                'query': row[0],
                'count': row[1],
                'avg_results': round(row[2], 1),
                'avg_time': round(row[3], 3)
            }
            for row in cursor
        ]
        
    def get_trending_categories(self, limit: int = 10) -> List[Dict]:
        """Get trending search categories"""
        cursor = self.conn.execute("""
            SELECT category, search_count
            FROM search_categories
            ORDER BY search_count DESC
            LIMIT ?
        """, (limit,))
        
        return [
            {'category': row[0], 'count': row[1]}
            for row in cursor
        ]
        
    def get_missing_docs_report(self, min_requests: int = 3) -> List[Dict]:
        """Get report of frequently searched but missing documentation"""
        cursor = self.conn.execute("""
            SELECT topic, query, request_count, first_requested, last_requested
            FROM missing_docs
            WHERE request_count >= ?
            ORDER BY request_count DESC
        """, (min_requests,))
        
        return [
            {
                'topic': row[0],
                'query': row[1],
                'requests': row[2],
                'first_requested': row[3],
                'last_requested': row[4]
            }
            for row in cursor
        ]
        
    def get_search_performance_stats(self) -> Dict:
        """Get overall search performance statistics"""
        # Total searches
        total_searches = self.conn.execute(
            "SELECT COUNT(*) FROM search_queries"
        ).fetchone()[0]
        
        # Average search time
        avg_time = self.conn.execute(
            "SELECT AVG(search_time) FROM search_queries"
        ).fetchone()[0] or 0
        
        # Searches with results
        with_results = self.conn.execute(
            "SELECT COUNT(*) FROM search_queries WHERE results_count > 0"
        ).fetchone()[0]
        
        # Average results per search
        avg_results = self.conn.execute(
            "SELECT AVG(results_count) FROM search_queries"
        ).fetchone()[0] or 0
        
        return {
            'total_searches': total_searches,
            'avg_search_time': round(avg_time, 3),
            'success_rate': round(with_results / total_searches * 100, 1) if total_searches > 0 else 0,
            'avg_results_per_search': round(avg_results, 1)
        }
        
    def generate_expansion_recommendations(self) -> List[Dict]:
        """Generate recommendations for documentation expansion based on analytics"""
        recommendations = []
        
        # Get missing docs
        missing = self.get_missing_docs_report(min_requests=5)
        if missing:
            recommendations.append({
                'type': 'missing_documentation',
                'priority': 'high',
                'description': 'Frequently searched topics with no results',
                'items': [m['topic'] for m in missing[:5]]
            })
            
        # Get trending categories
        trending = self.get_trending_categories(limit=5)
        recommendations.append({
            'type': 'trending_categories',
            'priority': 'medium',
            'description': 'Most searched categories - consider expanding',
            'items': trending
        })
        
        # Get low-result searches
        cursor = self.conn.execute("""
            SELECT query, avg_results_count 
            FROM popular_searches 
            WHERE avg_results_count < 5 AND search_count > 5
            ORDER BY search_count DESC
            LIMIT 10
        """)
        
        low_results = [{'query': row[0], 'avg_results': row[1]} for row in cursor]
        if low_results:
            recommendations.append({
                'type': 'low_result_queries',
                'priority': 'medium',
                'description': 'Popular searches with few results',
                'items': low_results
            })
            
        return recommendations


# CLI interface
if __name__ == "__main__":
    import sys
    
    analytics = SearchAnalytics()
    
    if len(sys.argv) < 2:
        print("Search Analytics Dashboard")
        print("=" * 60)
        
        # Performance stats
        stats = analytics.get_search_performance_stats()
        print(f"\nPerformance Stats:")
        print(f"  Total Searches: {stats['total_searches']}")
        print(f"  Success Rate: {stats['success_rate']}%")
        print(f"  Avg Search Time: {stats['avg_search_time']}s")
        print(f"  Avg Results: {stats['avg_results_per_search']}")
        
        # Popular searches
        print(f"\nTop 10 Popular Searches:")
        for i, search in enumerate(analytics.get_popular_searches(10), 1):
            print(f"  {i}. '{search['query']}' ({search['count']} times)")
            
        # Trending categories
        print(f"\nTrending Categories:")
        for cat in analytics.get_trending_categories(5):
            print(f"  • {cat['category']}: {cat['count']} searches")
            
        # Recommendations
        print(f"\nExpansion Recommendations:")
        for rec in analytics.generate_expansion_recommendations():
            print(f"\n  [{rec['priority'].upper()}] {rec['description']}:")
            if rec['type'] == 'trending_categories':
                for item in rec['items']:
                    print(f"    - {item['category']} ({item['count']} searches)")
            else:
                for item in rec['items'][:5]:
                    if isinstance(item, dict):
                        print(f"    - {item}")
                    else:
                        print(f"    - {item}")
    else:
        # Log a search from command line
        query = ' '.join(sys.argv[1:])
        analytics.log_search(query, 10, 0.123)  # Mock data
        print(f"Logged search: '{query}'")
