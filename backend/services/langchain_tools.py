from langchain.tools import Tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json

from .quiz_dataset_service import quiz_dataset_service
from .educational_api_service import educational_api_service

# Pydantic models for tool inputs
class QuizSearchInput(BaseModel):
    """Input for quiz search tools"""
    query: str = Field(description="Search query or topic")
    limit: Optional[int] = Field(default=5, description="Maximum number of results")

class QuizFilterInput(BaseModel):
    """Input for quiz filtering tool"""
    category: Optional[str] = Field(default=None, description="Filter by category (e.g., 'Standards specifications')")
    release: Optional[str] = Field(default=None, description="Filter by 3GPP release (e.g., '17', '18')")
    keyword: Optional[str] = Field(default=None, description="Filter by keyword in question text")
    limit: Optional[int] = Field(default=5, description="Maximum number of results")

class EducationalContentInput(BaseModel):
    """Input for educational content search"""
    topic: str = Field(description="Topic to search for educational content")

# Tool functions
def search_quiz_by_topic(query: str) -> str:
    """Search for quiz questions by topic/category"""
    try:
        results = quiz_dataset_service.search_by_topic(query)
        if not results:
            return f"No quiz questions found for topic: {query}"
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):
            formatted_results.append(f"{i}. {result['question']}")
        
        return f"Found {len(results)} quiz questions for topic '{query}':\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching quiz questions: {str(e)}"

def search_quiz_by_difficulty(release: str) -> str:
    """Search for quiz questions by difficulty level (3GPP release)"""
    try:
        results = quiz_dataset_service.search_by_difficulty(release)
        if not results:
            return f"No quiz questions found for 3GPP Release {release}"
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):
            formatted_results.append(f"{i}. {result['question']}")
        
        return f"Found {len(results)} quiz questions for 3GPP Release {release}:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching quiz questions: {str(e)}"

def search_quiz_by_keyword(keyword: str) -> str:
    """Search for quiz questions by keyword"""
    try:
        results = quiz_dataset_service.search_by_keyword(keyword)
        if not results:
            return f"No quiz questions found containing keyword: {keyword}"
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):
            formatted_results.append(f"{i}. {result['question']}")
        
        return f"Found {len(results)} quiz questions containing '{keyword}':\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error searching quiz questions: {str(e)}"

def get_random_quiz_questions(count: str = "5") -> str:
    """Get random quiz questions"""
    try:
        count_int = int(count)
        results = quiz_dataset_service.get_random_questions(count_int)
        if not results:
            return "No quiz questions available"
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"{i}. {result['question']}")
        
        return f"Random {len(results)} quiz questions:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error getting random quiz questions: {str(e)}"

def filter_quiz_questions(input_str: str) -> str:
    """Filter quiz questions by multiple criteria"""
    try:
        # Parse input string as JSON
        try:
            params = json.loads(input_str)
        except json.JSONDecodeError:
            # If not JSON, treat as simple keyword search
            params = {"keyword": input_str}
        
        category = params.get("category")
        release = params.get("release")
        keyword = params.get("keyword")
        limit = params.get("limit", 5)
        
        results = quiz_dataset_service.filter_questions(
            category=category,
            release=release,
            keyword=keyword,
            limit=limit
        )
        
        if not results:
            return f"No quiz questions found matching the criteria"
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(f"{i}. {result['question']}")
        
        filter_desc = []
        if category:
            filter_desc.append(f"category: {category}")
        if release:
            filter_desc.append(f"release: {release}")
        if keyword:
            filter_desc.append(f"keyword: {keyword}")
        
        filter_text = ", ".join(filter_desc) if filter_desc else "no filters"
        
        return f"Found {len(results)} quiz questions ({filter_text}):\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error filtering quiz questions: {str(e)}"

def get_quiz_categories() -> str:
    """Get all available quiz categories"""
    try:
        categories = quiz_dataset_service.get_all_categories()
        releases = quiz_dataset_service.get_all_releases()
        stats = quiz_dataset_service.get_dataset_stats()
        
        return f"""Available quiz categories: {', '.join(categories)}
Available 3GPP releases: {', '.join(releases)}
Total questions: {stats['total_questions']}
Questions with 4 options: {stats['questions_with_4_options']}
Questions with 5 options: {stats['questions_with_5_options']}"""
    except Exception as e:
        return f"Error getting quiz categories: {str(e)}"

def search_educational_content(topic: str) -> str:
    """Search for educational content from Khan Academy and other sources"""
    try:
        content = educational_api_service.get_educational_content_by_topic(topic)
        
        if content.get('error'):
            return f"Error getting educational content: {content['error']}"
        
        if not content.get('sources'):
            return f"No educational content found for topic: {topic}"
        
        formatted_sources = []
        for source in content['sources'][:3]:  # Limit to top 3 sources
            formatted_sources.append(f"- {source['title']}: {source['description']}")
        
        related_topics = content.get('related_topics', [])[:5]  # Limit to 5 related topics
        
        result = f"Educational content for '{topic}':\n"
        result += "\n".join(formatted_sources)
        
        if related_topics:
            result += f"\n\nRelated topics: {', '.join(related_topics)}"
        
        return result
    except Exception as e:
        return f"Error searching educational content: {str(e)}"

def get_khan_academy_topics() -> str:
    """Get available topics from Khan Academy"""
    try:
        topics = educational_api_service.get_khan_academy_topics()
        
        if not topics:
            return "No Khan Academy topics available"
        
        formatted_topics = []
        for topic in topics[:10]:  # Limit to top 10 topics
            formatted_topics.append(f"- {topic['title']}: {topic.get('description', 'No description')}")
        
        return f"Available Khan Academy topics:\n" + "\n".join(formatted_topics)
    except Exception as e:
        return f"Error getting Khan Academy topics: {str(e)}"

def get_educational_api_status() -> str:
    """Get status of educational APIs"""
    try:
        status = educational_api_service.get_api_status()
        
        khan_status = status.get('khan_academy', {})
        cache_size = status.get('cache_size', 0)
        
        return f"""Educational API Status:
Khan Academy: {khan_status.get('status', 'unknown')}
Cache size: {cache_size} items
Last updated: {status.get('last_updated', 'unknown')}"""
    except Exception as e:
        return f"Error getting API status: {str(e)}"

# Create LangChain tools
def create_quiz_tools() -> List[Tool]:
    """Create LangChain tools for quiz dataset operations"""
    
    tools = [
        Tool(
            name="search_quiz_by_topic",
            description="Search for quiz questions by topic or category. Use this to find questions related to specific subjects like 'Standards specifications' or 'Standards overview'.",
            func=search_quiz_by_topic
        ),
        Tool(
            name="search_quiz_by_difficulty",
            description="Search for quiz questions by difficulty level using 3GPP release numbers (14, 15, 16, 17, 18). Higher numbers indicate more recent and potentially more complex content.",
            func=search_quiz_by_difficulty
        ),
        Tool(
            name="search_quiz_by_keyword",
            description="Search for quiz questions containing specific keywords in the question text or explanation.",
            func=search_quiz_by_keyword
        ),
        Tool(
            name="get_random_quiz_questions",
            description="Get a random selection of quiz questions. Provide the number of questions as a string (e.g., '5').",
            func=get_random_quiz_questions
        ),
        Tool(
            name="filter_quiz_questions",
            description="Filter quiz questions by multiple criteria. Provide JSON string with 'category', 'release', 'keyword', and 'limit' parameters.",
            func=filter_quiz_questions
        ),
        Tool(
            name="get_quiz_categories",
            description="Get all available quiz categories, releases, and dataset statistics.",
            func=get_quiz_categories
        )
    ]
    
    return tools

def create_educational_api_tools() -> List[Tool]:
    """Create LangChain tools for educational API operations"""
    
    tools = [
        Tool(
            name="search_educational_content",
            description="Search for educational content from Khan Academy and other educational sources by topic.",
            func=search_educational_content
        ),
        Tool(
            name="get_khan_academy_topics",
            description="Get available topics from Khan Academy API.",
            func=get_khan_academy_topics
        ),
        Tool(
            name="get_educational_api_status",
            description="Get the current status of educational APIs including Khan Academy.",
            func=get_educational_api_status
        )
    ]
    
    return tools

def create_all_phase9_tools() -> List[Tool]:
    """Create all Phase 9 tools for LangChain agent"""
    quiz_tools = create_quiz_tools()
    educational_tools = create_educational_api_tools()
    
    return quiz_tools + educational_tools 