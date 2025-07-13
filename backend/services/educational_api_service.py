import requests
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
from urllib.parse import urlencode

class EducationalAPIService:
    """Service for integrating with educational APIs like Khan Academy"""
    
    def __init__(self):
        self.khan_academy_base_url = "https://www.khanacademy.org/api/v1"
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('timestamp')
        if not cached_time:
            return False
        
        return datetime.now() - cached_time < self.cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def get_khan_academy_topics(self) -> List[Dict[str, Any]]:
        """Get available topics from Khan Academy API"""
        cache_key = "khan_topics"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            url = f"{self.khan_academy_base_url}/topictree"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            topics = self._extract_topics_from_tree(data)
            
            self._set_cache(cache_key, topics)
            return topics
            
        except requests.RequestException as e:
            print(f"Error fetching Khan Academy topics: {e}")
            # Return fallback topics
            return self._get_fallback_topics()
    
    def _extract_topics_from_tree(self, tree_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract topics from Khan Academy topic tree"""
        topics = []
        
        def extract_recursive(node, parent_path=""):
            if not isinstance(node, dict):
                return
            
            node_id = node.get('id', '')
            title = node.get('title', '')
            kind = node.get('kind', '')
            
            if kind == 'Topic' and title:
                topic_path = f"{parent_path}/{title}" if parent_path else title
                topics.append({
                    'id': node_id,
                    'title': title,
                    'path': topic_path,
                    'kind': kind,
                    'description': node.get('description', ''),
                    'url': node.get('ka_url', '')
                })
            
            # Recursively process children
            children = node.get('children', [])
            for child in children:
                extract_recursive(child, f"{parent_path}/{title}" if parent_path else title)
        
        extract_recursive(tree_data)
        return topics
    
    def _get_fallback_topics(self) -> List[Dict[str, Any]]:
        """Fallback topics when API is unavailable"""
        return [
            {
                'id': 'math',
                'title': 'Mathematics',
                'path': 'Mathematics',
                'kind': 'Topic',
                'description': 'Mathematical concepts and problem solving',
                'url': 'https://www.khanacademy.org/math'
            },
            {
                'id': 'science',
                'title': 'Science',
                'path': 'Science',
                'kind': 'Topic',
                'description': 'Scientific concepts and experiments',
                'url': 'https://www.khanacademy.org/science'
            },
            {
                'id': 'computing',
                'title': 'Computing',
                'path': 'Computing',
                'kind': 'Topic',
                'description': 'Computer science and programming',
                'url': 'https://www.khanacademy.org/computing'
            },
            {
                'id': 'economics',
                'title': 'Economics',
                'path': 'Economics',
                'kind': 'Topic',
                'description': 'Economic principles and finance',
                'url': 'https://www.khanacademy.org/economics-finance-domain'
            }
        ]
    
    def search_khan_academy_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Khan Academy content"""
        cache_key = f"khan_search_{query}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Khan Academy doesn't have a public search API, so we'll simulate
            # In a real implementation, you'd use their actual search endpoint
            topics = self.get_khan_academy_topics()
            
            # Simple keyword matching
            query_lower = query.lower()
            matching_topics = []
            
            for topic in topics:
                title_lower = topic['title'].lower()
                desc_lower = topic.get('description', '').lower()
                
                if query_lower in title_lower or query_lower in desc_lower:
                    matching_topics.append(topic)
                
                if len(matching_topics) >= limit:
                    break
            
            self._set_cache(cache_key, matching_topics)
            return matching_topics
            
        except Exception as e:
            print(f"Error searching Khan Academy content: {e}")
            return []
    
    def get_educational_content_by_topic(self, topic: str) -> Dict[str, Any]:
        """Get educational content for a specific topic"""
        cache_key = f"content_{topic}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Search for content related to the topic
            search_results = self.search_khan_academy_content(topic, limit=5)
            
            content = {
                'topic': topic,
                'sources': [],
                'related_topics': [],
                'difficulty_levels': ['beginner', 'intermediate', 'advanced']
            }
            
            for result in search_results:
                content['sources'].append({
                    'title': result['title'],
                    'url': result['url'],
                    'description': result.get('description', ''),
                    'source': 'Khan Academy'
                })
                
                # Extract related topics from the path
                path_parts = result['path'].split('/')
                for part in path_parts:
                    if part != result['title'] and part not in content['related_topics']:
                        content['related_topics'].append(part)
            
            self._set_cache(cache_key, content)
            return content
            
        except Exception as e:
            print(f"Error getting educational content: {e}")
            return {
                'topic': topic,
                'sources': [],
                'related_topics': [],
                'difficulty_levels': ['beginner', 'intermediate', 'advanced'],
                'error': str(e)
            }
    
    async def get_multiple_topics_async(self, topics: List[str]) -> Dict[str, Any]:
        """Asynchronously get content for multiple topics"""
        async def fetch_topic(session, topic):
            try:
                # In a real implementation, this would make async HTTP requests
                # For now, we'll simulate with the sync method
                return topic, self.get_educational_content_by_topic(topic)
            except Exception as e:
                return topic, {'error': str(e)}
        
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_topic(session, topic) for topic in topics]
            responses = await asyncio.gather(*tasks)
            
            for topic, content in responses:
                results[topic] = content
        
        return results
    
    def get_difficulty_suggestions(self, topic: str, current_level: str = 'beginner') -> List[str]:
        """Get difficulty level suggestions for a topic"""
        difficulty_map = {
            'beginner': ['intermediate'],
            'intermediate': ['beginner', 'advanced'],
            'advanced': ['intermediate']
        }
        
        return difficulty_map.get(current_level, ['beginner'])
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of educational APIs"""
        status = {
            'khan_academy': self._check_khan_academy_status(),
            'cache_size': len(self.cache),
            'last_updated': datetime.now().isoformat()
        }
        
        return status
    
    def _check_khan_academy_status(self) -> Dict[str, Any]:
        """Check Khan Academy API status"""
        try:
            response = requests.get(f"{self.khan_academy_base_url}/topictree", timeout=5)
            return {
                'status': 'available' if response.status_code == 200 else 'unavailable',
                'response_time': response.elapsed.total_seconds(),
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unavailable',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def clear_cache(self) -> None:
        """Clear the API cache"""
        self.cache.clear()

# Global instance
educational_api_service = EducationalAPIService() 