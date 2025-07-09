"""
Web Search Agent - Handles web search queries using Brave Search API
"""
import requests
import json
from typing import Dict, Any, Optional
from openai import AzureOpenAI

class WebSearchAgent:
    def __init__(self, brave_api_key: str, openai_client: AzureOpenAI, model: str):
        """
        Initialize the Web Search Agent
        
        Args:
            brave_api_key: Brave Search API key
            openai_client: Azure OpenAI client
            model: Model name to use
        """
        self.brave_api_key = brave_api_key
        self.client = openai_client
        self.model = model
        self.agent_name = "web_search"
    
    def brave_search(self, query: str, count: int = 5) -> Optional[Dict[str, Any]]:
        """
        Perform a web search using the Brave Search API
        
        Args:
            query: The search query
            count: Number of results to return
            
        Returns:
            JSON response from the API or None if error
        """
        url = "https://api.search.brave.com/res/v1/web/search"
        
        try:
            response = requests.get(
                url,
                headers={"X-Subscription-Token": self.brave_api_key},
                params={
                    "q": query,
                    "count": count,
                    "country": "us",
                    "search_lang": "en",
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Brave Search API error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def extract_search_info(self, search_results: Dict[str, Any], max_results: int = 3) -> str:
        """
        Extract and format relevant information from search results
        
        Args:
            search_results: JSON response from Brave Search API
            max_results: Maximum number of results to extract
            
        Returns:
            Formatted string with extracted information
        """
        if not search_results or 'web' not in search_results:
            return "No search results found."
        
        extracted_info = []
        
        # Get basic search info
        query = search_results.get('query', {}).get('query', 'Unknown query')
        extracted_info.append(f"Search query: {query}")
        
        # Extract relevant information from each result
        results = search_results.get('web', {}).get('results', [])
        
        for i, result in enumerate(results[:max_results]):
            title = result.get('title', 'No title')
            url = result.get('url', 'No URL')
            description = result.get('description', 'No description')
            
            extracted_info.append(f"\n[{i+1}] {title}")
            extracted_info.append(f"URL: {url}")
            extracted_info.append(f"Summary: {description}")
        
        return "\n".join(extracted_info)
    
    def generate_response(self, query: str, search_context: str) -> str:
        """
        Generate a response based on the search results
        
        Args:
            query: Original user query
            search_context: Formatted search results
            
        Returns:
            Generated response
        """
        prompt = f"""
        Based on the following web search results, please provide a comprehensive answer to the user's question.

        USER QUESTION: {query}

        SEARCH RESULTS:
        {search_context}

        Please provide a helpful answer based on the search results. If the search results don't contain 
        relevant information, please state that clearly. Always cite your sources by mentioning the websites 
        or sources from the search results.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that answers questions based on web search results. Always cite your sources and be accurate."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a web search query and return response
        
        Args:
            query: User's query
            
        Returns:
            Response dictionary with search results and generated response
        """
        try:
            # Perform web search
            search_results = self.brave_search(query)
            
            if not search_results:
                return {
                    "response": "Sorry, I couldn't perform the web search at this time. Please try again later.",
                    "agent": self.agent_name,
                    "error": "Web search failed",
                    "sources": []
                }
            
            # Extract search information
            search_context = self.extract_search_info(search_results)
            
            # Generate response based on search results
            response = self.generate_response(query, search_context)
            
            # Extract sources for citation
            sources = []
            web_results = search_results.get('web', {}).get('results', [])
            for result in web_results[:3]:  # Top 3 sources
                sources.append({
                    "title": result.get('title', 'No title'),
                    "url": result.get('url', 'No URL'),
                    "description": result.get('description', 'No description')[:100] + "..."
                })
            
            return {
                "response": response,
                "agent": self.agent_name,
                "sources": sources,
                "search_query": query,
                "search_context": search_context
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error while searching: {str(e)}",
                "agent": self.agent_name,
                "error": str(e),
                "sources": []
            }
    
    def test_connection(self) -> bool:
        """
        Test if the Brave Search API is working
        
        Returns:
            True if API is working, False otherwise
        """
        try:
            test_results = self.brave_search("test query", count=1)
            return test_results is not None
        except Exception:
            return False
