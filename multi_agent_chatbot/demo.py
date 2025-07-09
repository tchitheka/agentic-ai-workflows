"""
Demonstration script for the multi-agent chatbot
Run this to see how the system works without the Streamlit interface
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from utils.memory import ConversationMemory
from agents.router_agent import RouterAgent
from agents.web_search_agent import WebSearchAgent
from agents.sql_agent import SQLAgent
from agents.document_agent import DocumentAgent
from openai import AzureOpenAI

def setup_system():
    """Set up the multi-agent system"""
    print("🔧 Setting up multi-agent system...")
    
    try:
        # Create OpenAI client
        openai_client = AzureOpenAI(
            default_headers={"Ocp-Apim-Subscription-Key": settings.openai_key},
            api_key=settings.openai_key,
            azure_endpoint=settings.openai_endpoint,
            azure_deployment=settings.openai_deployment,
            api_version=settings.openai_api_version,
        )
        
        # Initialize memory
        memory = ConversationMemory()
        
        # Initialize router
        router = RouterAgent(openai_client, settings.openai_model)
        
        # Initialize and register agents
        agents_initialized = 0
        
        # Web Search Agent
        try:
            web_agent = WebSearchAgent(
                settings.brave_search_key,
                openai_client,
                settings.openai_model
            )
            router.register_agent("web_search", web_agent)
            agents_initialized += 1
        except Exception as e:
            print(f"⚠️ Web Search Agent failed: {e}")
        
        # SQL Agent
        try:
            sql_agent = SQLAgent(
                settings.database_path,
                openai_client,
                settings.openai_model
            )
            router.register_agent("sql", sql_agent)
            agents_initialized += 1
        except Exception as e:
            print(f"⚠️ SQL Agent failed: {e}")
        
        # Document Agent
        try:
            document_agent = DocumentAgent(
                settings.documents_path,
                openai_client,
                settings.openai_model,
                settings.get_embeddings_client_config(),
                settings.get_openai_client_config()
            )
            router.register_agent("document", document_agent)
            agents_initialized += 1
        except Exception as e:
            print(f"⚠️ Document Agent failed: {e}")
        
        print(f"✅ System initialized with {agents_initialized} agents")
        return router, memory
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return None, None

def demonstrate_routing():
    """Demonstrate the routing system"""
    print("\n🎯 Demonstrating routing system...")
    
    router, memory = setup_system()
    if not router:
        print("❌ Cannot demonstrate routing - system setup failed")
        return
    
    # Test queries with their expected agents
    test_queries = [
        ("What's the weather like today?", "web_search"),
        ("How many customers do we have?", "sql"),
        ("Summarize the documents", "document"),
        ("Bitcoin price today", "web_search"),
        ("Show me all products", "sql"),
        ("What are the main concepts in the documents?", "document"),
        ("Latest news about AI", "web_search"),
        ("Total revenue from orders", "sql"),
        ("Explain the key topics", "document"),
    ]
    
    print("\nRouting decisions:")
    print("-" * 50)
    
    for query, expected in test_queries:
        actual = router.route_query(query)
        status = "✅" if actual == expected else "⚠️"
        print(f"{status} '{query}' -> {actual}")
    
    return router, memory

def interactive_demo():
    """Interactive demonstration"""
    print("\n💬 Interactive Demo")
    print("=" * 50)
    print("Ask questions to see how the multi-agent system works!")
    print("Examples:")
    print("- What's the weather today? (web search)")
    print("- How many customers do we have? (database)")
    print("- Summarize the documents (document analysis)")
    print("- Type 'quit' to exit")
    print()
    
    router, memory = setup_system()
    if not router:
        print("❌ Cannot run interactive demo - system setup failed")
        return
    
    while True:
        try:
            query = input("🧑 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Show routing decision
            routing_info = router.explain_routing(query)
            print(f"🎯 Routing to: {routing_info['selected_agent']} agent")
            
            # Process query
            print("🤖 Processing...")
            response = router.process_query(query)
            
            # Display response
            print(f"🤖 {response['agent'].title()} Agent: {response['response']}")
            
            # Show additional info based on agent type
            if response['agent'] == 'sql' and 'sql_query' in response:
                print(f"📝 SQL Query: {response['sql_query']}")
                if 'data' in response and response['data'] is not None:
                    print(f"📊 Results: {len(response['data'])} rows")
            
            elif response['agent'] == 'web_search' and 'sources' in response:
                print(f"🔗 Sources: {len(response['sources'])} found")
            
            elif response['agent'] == 'document' and 'sources' in response:
                print(f"📚 Document sources: {len(response['sources'])} found")
            
            # Add to memory
            memory.add_message("user", query)
            memory.add_message("assistant", response['response'], response)
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Demo completed!")
    
    # Show conversation stats
    stats = memory.get_stats()
    print(f"\n📊 Conversation Stats:")
    print(f"Total messages: {stats['total_messages']}")
    print(f"Agent usage: {stats['agent_usage']}")

def main():
    """Main demonstration function"""
    print("🚀 Multi-Agent Chatbot Demonstration")
    print("=" * 50)
    
    # Check configuration
    try:
        settings.validate_config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required keys are set.")
        return
    
    # Demonstrate routing
    demonstrate_routing()
    
    # Interactive demo
    interactive_demo()

if __name__ == "__main__":
    main()
