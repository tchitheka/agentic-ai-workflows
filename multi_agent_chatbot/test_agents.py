"""
Test script for multi-agent chatbot
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from agents.router_agent import RouterAgent
from agents.web_search_agent import WebSearchAgent
from agents.sql_agent import SQLAgent
from agents.document_agent import DocumentAgent
from openai import AzureOpenAI

def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    try:
        settings.validate_config()
        print("✅ Configuration valid")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_agents():
    """Test agent initialization"""
    print("\n🤖 Testing agent initialization...")
    
    try:
        # Create OpenAI client
        openai_client = AzureOpenAI(
            default_headers={"Ocp-Apim-Subscription-Key": settings.openai_key},
            api_key=settings.openai_key,
            azure_endpoint=settings.openai_endpoint,
            azure_deployment=settings.openai_deployment,
            api_version=settings.openai_api_version,
        )
        
        # Initialize router
        router = RouterAgent(openai_client, settings.openai_model)
        
        # Test Web Search Agent
        try:
            web_agent = WebSearchAgent(
                settings.brave_search_key,
                openai_client,
                settings.openai_model
            )
            if web_agent.test_connection():
                print("✅ Web Search Agent initialized and connected")
                router.register_agent("web_search", web_agent)
            else:
                print("⚠️ Web Search Agent initialized but connection failed")
        except Exception as e:
            print(f"❌ Web Search Agent error: {e}")
        
        # Test SQL Agent
        try:
            sql_agent = SQLAgent(
                settings.database_path,
                openai_client,
                settings.openai_model
            )
            if sql_agent.test_connection():
                print("✅ SQL Agent initialized and connected")
                router.register_agent("sql", sql_agent)
            else:
                print("⚠️ SQL Agent initialized but database connection failed")
        except Exception as e:
            print(f"❌ SQL Agent error: {e}")
        
        # Test Document Agent
        try:
            document_agent = DocumentAgent(
                settings.documents_path,
                openai_client,
                settings.openai_model,
                settings.get_embeddings_client_config(),
                settings.get_openai_client_config()
            )
            if document_agent.test_connection():
                print("✅ Document Agent initialized and connected")
                router.register_agent("document", document_agent)
            else:
                print("⚠️ Document Agent initialized but no documents loaded")
        except Exception as e:
            print(f"❌ Document Agent error: {e}")
        
        return router
        
    except Exception as e:
        print(f"❌ Agent initialization error: {e}")
        return None

def test_routing():
    """Test routing logic"""
    print("\n🎯 Testing routing logic...")
    
    router = test_agents()
    if not router:
        print("❌ Cannot test routing - agent initialization failed")
        return
    
    # Test queries
    test_queries = [
        ("What's the weather today?", "web_search"),
        ("How many customers do we have?", "sql"),
        ("Summarize the documents", "document"),
        ("Bitcoin price", "web_search"),
        ("Show me sales data", "sql"),
        ("Explain the concept", "document")
    ]
    
    for query, expected_agent in test_queries:
        actual_agent = router.route_query(query)
        status = "✅" if actual_agent == expected_agent else "⚠️"
        print(f"{status} '{query}' -> {actual_agent} (expected: {expected_agent})")

def test_sample_queries():
    """Test sample queries with each agent"""
    print("\n💬 Testing sample queries...")
    
    router = test_agents()
    if not router:
        print("❌ Cannot test queries - agent initialization failed")
        return
    
    # Test a simple query from each agent
    test_queries = [
        "What is artificial intelligence?",  # Should go to web_search
        "How many products are there?",     # Should go to sql
        "What are the main topics?",        # Should go to document
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            response = router.process_query(query)
            print(f"✅ Agent: {response.get('agent', 'unknown')}")
            print(f"📝 Response: {response.get('response', 'No response')[:100]}...")
        except Exception as e:
            print(f"❌ Query failed: {e}")

def main():
    """Main test function"""
    print("🧪 Multi-Agent Chatbot Test Suite")
    print("=" * 50)
    
    # Test configuration
    if not test_configuration():
        print("\n❌ Configuration test failed. Please check your .env file.")
        return
    
    # Test agents
    test_agents()
    
    # Test routing
    test_routing()
    
    # Test sample queries
    test_sample_queries()
    
    print("\n🎉 Test suite completed!")
    print("You can now run the Streamlit app with: streamlit run app.py")

if __name__ == "__main__":
    main()
