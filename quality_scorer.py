"""
Documentation quality scoring system
Evaluates and scores repositories based on documentation quality metrics
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import json

class QualityScorer:
    def __init__(self):
        self.weights = {
            'completeness': 0.25,      # How complete is the documentation
            'freshness': 0.20,         # How recently updated
            'structure': 0.20,         # Organization and structure
            'examples': 0.15,          # Code examples and tutorials
            'community': 0.10,         # Community engagement
            'accessibility': 0.10      # Ease of access and navigation
        }
        
    def score_repository(self, repo_data: dict, documents: List[dict]) -> Dict[str, float]:
        """Score a repository's documentation quality"""
        scores = {
            'completeness': self._score_completeness(repo_data, documents),
            'freshness': self._score_freshness(repo_data, documents),
            'structure': self._score_structure(documents),
            'examples': self._score_examples(documents),
            'community': self._score_community(repo_data),
            'accessibility': self._score_accessibility(documents)
        }
        
        # Calculate weighted total
        total_score = sum(scores[metric] * self.weights[metric] for metric in scores)
        
        return {
            'total_score': round(total_score, 2),
            'metrics': scores,
            'grade': self._get_grade(total_score)
        }
        
    def _score_completeness(self, repo_data: dict, documents: List[dict]) -> float:
        """Score based on documentation completeness"""
        score = 0.0
        
        # Check for essential files
        doc_paths = [doc['path'].lower() for doc in documents]
        
        # README is essential
        if any('readme' in path for path in doc_paths):
            score += 0.3
            
        # Look for comprehensive documentation
        doc_indicators = ['docs/', 'documentation/', 'wiki/', 'guide/']
        if any(indicator in path for path in doc_paths for indicator in doc_indicators):
            score += 0.2
            
        # API documentation
        if any('api' in path for path in doc_paths):
            score += 0.1
            
        # Installation/setup guide
        if any(keyword in ' '.join(doc_paths) for keyword in ['install', 'setup', 'getting-started']):
            score += 0.1
            
        # Contributing guidelines
        if any('contributing' in path for path in doc_paths):
            score += 0.1
            
        # Examples or tutorials
        if any(keyword in ' '.join(doc_paths) for keyword in ['example', 'tutorial', 'sample']):
            score += 0.1
            
        # Changelog
        if any('changelog' in path or 'history' in path for path in doc_paths):
            score += 0.1
            
        return min(score, 1.0)
        
    def _score_freshness(self, repo_data: dict, documents: List[dict]) -> float:
        """Score based on how recently documentation was updated"""
        # Check repo last push date
        last_push = repo_data.get('pushed_at', '')
        if last_push:
            try:
                push_date = datetime.strptime(last_push[:10], '%Y-%m-%d')
                days_ago = (datetime.now() - push_date).days
                
                if days_ago < 30:
                    return 1.0
                elif days_ago < 90:
                    return 0.8
                elif days_ago < 180:
                    return 0.6
                elif days_ago < 365:
                    return 0.4
                else:
                    return 0.2
            except:
                pass
                
        return 0.5  # Default middle score
        
    def _score_structure(self, documents: List[dict]) -> float:
        """Score based on documentation organization"""
        score = 0.0
        
        # Look for structured documentation
        if len(documents) > 5:
            score += 0.3  # Multiple documentation files
            
        # Check for hierarchical organization
        paths = [doc['path'] for doc in documents]
        depth_scores = []
        for path in paths:
            depth = path.count('/')
            if depth > 0:
                depth_scores.append(min(depth * 0.1, 0.3))
                
        if depth_scores:
            score += sum(depth_scores) / len(depth_scores)
            
        # Look for index or table of contents
        content_combined = ' '.join(doc.get('content', '')[:1000] for doc in documents)
        if any(indicator in content_combined.lower() for indicator in ['table of contents', 'index', '## contents']):
            score += 0.2
            
        # Check for sections and headers
        header_count = len(re.findall(r'^#{1,6}\s', content_combined, re.MULTILINE))
        if header_count > 10:
            score += 0.2
            
        return min(score, 1.0)
        
    def _score_examples(self, documents: List[dict]) -> float:
        """Score based on code examples and tutorials"""
        score = 0.0
        
        content_combined = ' '.join(doc.get('content', '')[:5000] for doc in documents)
        
        # Count code blocks
        code_blocks = len(re.findall(r'```[\s\S]*?```', content_combined))
        score += min(code_blocks * 0.05, 0.4)
        
        # Look for example keywords
        example_keywords = ['example', 'sample', 'demo', 'tutorial', 'quickstart', 'getting started']
        keyword_count = sum(content_combined.lower().count(keyword) for keyword in example_keywords)
        score += min(keyword_count * 0.02, 0.3)
        
        # Check for interactive elements (links to demos, playgrounds)
        if any(keyword in content_combined.lower() for keyword in ['playground', 'codesandbox', 'stackblitz', 'demo']):
            score += 0.2
            
        # Inline code snippets
        inline_code = len(re.findall(r'`[^`]+`', content_combined))
        score += min(inline_code * 0.01, 0.1)
        
        return min(score, 1.0)
        
    def _score_community(self, repo_data: dict) -> float:
        """Score based on community engagement"""
        score = 0.0
        
        # Stars (popularity)
        stars = repo_data.get('stargazers_count', 0)
        if stars > 10000:
            score += 0.4
        elif stars > 1000:
            score += 0.3
        elif stars > 100:
            score += 0.2
        elif stars > 10:
            score += 0.1
            
        # Has topics/tags
        if repo_data.get('topics'):
            score += 0.2
            
        # Has description
        if repo_data.get('description'):
            score += 0.2
            
        # License
        if repo_data.get('license'):
            score += 0.2
            
        return min(score, 1.0)
        
    def _score_accessibility(self, documents: List[dict]) -> float:
        """Score based on ease of access and navigation"""
        score = 0.0
        
        # README at root
        if any(doc['path'].lower() in ['readme.md', 'readme.rst', 'readme.txt'] for doc in documents):
            score += 0.4
            
        # Clear file naming
        clear_names = ['install', 'setup', 'guide', 'tutorial', 'api', 'reference']
        matching_files = sum(1 for doc in documents if any(name in doc['path'].lower() for name in clear_names))
        score += min(matching_files * 0.1, 0.3)
        
        # Not too many files (overwhelming)
        if 3 <= len(documents) <= 20:
            score += 0.3
        elif len(documents) > 20:
            score += 0.1  # Too many can be overwhelming
            
        return min(score, 1.0)
        
    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 0.9:
            return 'A+'
        elif score >= 0.85:
            return 'A'
        elif score >= 0.80:
            return 'A-'
        elif score >= 0.75:
            return 'B+'
        elif score >= 0.70:
            return 'B'
        elif score >= 0.65:
            return 'B-'
        elif score >= 0.60:
            return 'C+'
        elif score >= 0.55:
            return 'C'
        elif score >= 0.50:
            return 'C-'
        elif score >= 0.40:
            return 'D'
        else:
            return 'F'
            
    def generate_improvement_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """Generate suggestions for improving documentation"""
        suggestions = []
        metrics = scores.get('metrics', {})
        
        if metrics.get('completeness', 0) < 0.7:
            suggestions.append("Add more comprehensive documentation including API references and guides")
            
        if metrics.get('freshness', 0) < 0.5:
            suggestions.append("Update documentation to reflect recent changes")
            
        if metrics.get('structure', 0) < 0.6:
            suggestions.append("Organize documentation with clear hierarchy and table of contents")
            
        if metrics.get('examples', 0) < 0.5:
            suggestions.append("Add more code examples and tutorials")
            
        if metrics.get('community', 0) < 0.5:
            suggestions.append("Improve repository metadata: add topics, description, and license")
            
        if metrics.get('accessibility', 0) < 0.6:
            suggestions.append("Ensure README is present and use clear, descriptive file names")
            
        return suggestions


# Command-line interface
if __name__ == "__main__":
    import sys
    from database import Database
    
    if len(sys.argv) < 2:
        print("Usage: python quality_scorer.py <repository_name>")
        sys.exit(1)
        
    repo_name = sys.argv[1]
    db = Database("unified_docs.db")
    
    # Get repository data
    repo = db.get_repository_by_name(repo_name)
    if not repo:
        print(f"Repository {repo_name} not found")
        sys.exit(1)
        
    # Get documents
    docs = db.get_repository_documents(repo_name)
    
    # Score the repository
    scorer = QualityScorer()
    scores = scorer.score_repository(repo, docs)
    
    print(f"\nQuality Score for {repo_name}")
    print("=" * 50)
    print(f"Overall Grade: {scores['grade']} ({scores['total_score']:.2f}/1.00)")
    print("\nDetailed Metrics:")
    for metric, score in scores['metrics'].items():
        print(f"  {metric.capitalize()}: {score:.2f}/1.00")
        
    suggestions = scorer.generate_improvement_suggestions(scores)
    if suggestions:
        print("\nImprovement Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
