#!/usr/bin/env python3
"""
Quick test script for the Simple Multi-Agent Chatbot
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_agent import SimpleAgent

def test_agent():
    """Test the simple agent with sample queries"""
    print("🧪 Testing Simple Multi-Agent Chatbot")
    print("=" * 50)
    
    # Initialize agent
    agent = SimpleAgent()
    
    # Test queries
    test_queries = [
        "How many customers do we have?",
        "What's the weather today?",
        "Summarize the documents"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        print("-" * 30)
        
        response = agent.process_query(query)
        print(f"✅ Response: {response[:200]}...")
        
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_agent()
