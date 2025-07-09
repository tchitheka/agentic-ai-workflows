"""
Simple conversation memory system for multi-agent chatbot
"""
from datetime import datetime
from typing import List, Dict, Optional, Any

class ConversationMemory:
    def __init__(self, max_messages: int = 50):
        """
        Initialize conversation memory
        
        Args:
            max_messages: Maximum number of messages to store
        """
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a message to the conversation history
        
        Args:
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
            metadata: Additional metadata (agent used, sources, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        # Trim messages if we exceed max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history
        
        Returns:
            List of message dictionaries
        """
        return self.messages.copy()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent messages
        
        Args:
            count: Number of recent messages to retrieve
            
        Returns:
            List of recent message dictionaries
        """
        return self.messages[-count:]
    
    def get_context_for_llm(self, max_context_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM
        
        Args:
            max_context_messages: Maximum number of messages to include in context
            
        Returns:
            List of messages formatted for OpenAI chat completions
        """
        recent_messages = self.get_recent_messages(max_context_messages)
        
        formatted_messages = []
        for msg in recent_messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return formatted_messages
    
    def clear(self):
        """Clear all conversation history"""
        self.messages = []
    
    def search_messages(self, query: str, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for messages containing specific text
        
        Args:
            query: Text to search for
            role: Optional role filter ('user' or 'assistant')
            
        Returns:
            List of matching messages
        """
        results = []
        
        for msg in self.messages:
            # Check role filter
            if role and msg["role"] != role:
                continue
            
            # Check if query is in content (case-insensitive)
            if query.lower() in msg["content"].lower():
                results.append(msg)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the conversation
        
        Returns:
            Dictionary with conversation statistics
        """
        if not self.messages:
            return {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
        
        user_count = sum(1 for msg in self.messages if msg["role"] == "user")
        assistant_count = sum(1 for msg in self.messages if msg["role"] == "assistant")
        
        # Count agent usage
        agent_usage = {}
        for msg in self.messages:
            if msg["role"] == "assistant" and "metadata" in msg:
                agent = msg["metadata"].get("agent", "unknown")
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        return {
            "total_messages": len(self.messages),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "agent_usage": agent_usage,
            "first_message_time": self.messages[0]["timestamp"] if self.messages else None,
            "last_message_time": self.messages[-1]["timestamp"] if self.messages else None
        }
