"""
Router Agent - Routes user queries to appropriate specialized agents
"""
import re
from typing import Dict, Any, Optional
from openai import AzureOpenAI

class RouterAgent:
    def __init__(self, openai_client: AzureOpenAI, model: str):
        """
        Initialize the Router Agent
        
        Args:
            openai_client: Azure OpenAI client
            model: Model name to use
        """
        self.client = openai_client
        self.model = model
        self.agents = {}
        
        # Define routing keywords for simple keyword-based routing
        self.routing_keywords = {
            "web_search": [
                "current", "latest", "recent", "today", "now", "news", "weather", 
                "price", "stock", "trending", "happening", "update", "breaking",
                "real-time", "live", "fresh", "new", "this week", "this month",
                "compare prices", "market", "bitcoin", "crypto"
            ],
            "sql": [
                "data", "database", "customers", "orders", "products", "sales", 
                "count", "total", "sum", "average", "revenue", "profit",
                "table", "records", "rows", "columns", "query", "search database",
                "how many", "show me", "list all", "find in database",
                "customer data", "order data", "product data", "sales data"
            ],
            "document": [
                "document", "documents", "explain", "definition", "concept", 
                "summary", "summarize", "analyze", "analysis", "text",
                "content", "information", "details", "description", "meaning",
                "what is", "tell me about", "describe", "overview", "review",
                "file", "paper", "report", "study", "research"
            ]
        }
    
    def register_agent(self, name: str, agent):
        """
        Register a specialized agent
        
        Args:
            name: Name of the agent ('web_search', 'sql', 'document')
            agent: Agent instance
        """
        self.agents[name] = agent
        print(f"✅ Registered {name} agent")
    
    def route_query(self, query: str) -> str:
        """
        Determine which agent should handle the query using keyword matching
        
        Args:
            query: User's query
            
        Returns:
            Agent name that should handle the query
        """
        query_lower = query.lower()
        
        # Score each agent based on keyword matches
        scores = {}
        
        for agent_name, keywords in self.routing_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_lower:
                    # Give higher weight to longer, more specific keywords
                    score += len(keyword.split())
            scores[agent_name] = score
        
        # If no keywords matched, use fallback logic
        if all(score == 0 for score in scores.values()):
            return self._fallback_routing(query)
        
        # Return the agent with the highest score
        best_agent = max(scores, key=scores.get)
        return best_agent
    
    def _fallback_routing(self, query: str) -> str:
        """
        Fallback routing logic when no keywords match
        
        Args:
            query: User's query
            
        Returns:
            Default agent name
        """
        # Simple heuristics for fallback
        if "?" in query:
            # Questions often benefit from web search for current info
            return "web_search"
        elif any(word in query.lower() for word in ["what", "how", "why", "when", "where"]):
            # General questions - try document first, then web
            return "document"
        else:
            # Default to web search
            return "web_search"
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Route query to appropriate agent and return response
        
        Args:
            query: User's query
            
        Returns:
            Response dictionary with agent response and metadata
        """
        # Determine which agent to use
        agent_name = self.route_query(query)
        
        # Check if agent is registered
        if agent_name not in self.agents:
            return {
                "response": f"Sorry, the {agent_name} agent is not available.",
                "agent": "router",
                "error": f"Agent {agent_name} not registered",
                "routing_decision": agent_name
            }
        
        try:
            # Get the agent and process the query
            agent = self.agents[agent_name]
            response = agent.process_query(query)
            
            # Add routing metadata
            response["routing_decision"] = agent_name
            
            return response
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error while processing your query: {str(e)}",
                "agent": agent_name,
                "error": str(e),
                "routing_decision": agent_name
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all registered agents
        
        Returns:
            Dictionary with agent status information
        """
        status = {
            "registered_agents": list(self.agents.keys()),
            "available_agents": len(self.agents),
            "routing_keywords": self.routing_keywords
        }
        
        return status
    
    def explain_routing(self, query: str) -> Dict[str, Any]:
        """
        Explain why a query would be routed to a specific agent
        
        Args:
            query: User's query
            
        Returns:
            Explanation of routing decision
        """
        agent_name = self.route_query(query)
        query_lower = query.lower()
        
        # Find matched keywords
        matched_keywords = []
        for keyword in self.routing_keywords.get(agent_name, []):
            if keyword in query_lower:
                matched_keywords.append(keyword)
        
        explanation = {
            "query": query,
            "selected_agent": agent_name,
            "matched_keywords": matched_keywords,
            "reasoning": f"Query routed to {agent_name} agent"
        }
        
        if matched_keywords:
            explanation["reasoning"] += f" based on keywords: {', '.join(matched_keywords)}"
        else:
            explanation["reasoning"] += " using fallback logic"
        
        return explanation
