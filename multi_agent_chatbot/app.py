"""
Multi-Agent Chatbot - Main Streamlit Application
"""
import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our components
from config.settings import settings
from utils.memory import ConversationMemory
from agents.router_agent import RouterAgent
from agents.web_search_agent import WebSearchAgent
from agents.sql_agent import SQLAgent
from agents.document_agent import DocumentAgent

# OpenAI client
from openai import AzureOpenAI

def initialize_session_state():
    """Initialize session state variables"""
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationMemory()
    
    if 'router' not in st.session_state:
        st.session_state.router = None
    
    if 'agents_initialized' not in st.session_state:
        st.session_state.agents_initialized = False
    
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None

def initialize_agents():
    """Initialize all agents"""
    try:
        # Validate configuration
        settings.validate_config()
        
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
        
        # Initialize and register agents
        st.write("🔧 Initializing agents...")
        
        # Web Search Agent
        try:
            web_agent = WebSearchAgent(
                settings.brave_search_key,
                openai_client,
                settings.openai_model
            )
            router.register_agent("web_search", web_agent)
            st.write("✅ Web Search Agent initialized")
        except Exception as e:
            st.warning(f"⚠️ Web Search Agent failed to initialize: {str(e)}")
        
        # SQL Agent
        try:
            sql_agent = SQLAgent(
                settings.database_path,
                openai_client,
                settings.openai_model
            )
            router.register_agent("sql", sql_agent)
            st.write("✅ SQL Agent initialized")
        except Exception as e:
            st.warning(f"⚠️ SQL Agent failed to initialize: {str(e)}")
        
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
            st.write("✅ Document Agent initialized")
        except Exception as e:
            st.warning(f"⚠️ Document Agent failed to initialize: {str(e)}")
        
        st.session_state.router = router
        st.session_state.agents_initialized = True
        st.success("🎉 All agents initialized successfully!")
        
    except Exception as e:
        st.session_state.error_message = f"Failed to initialize agents: {str(e)}"
        st.error(st.session_state.error_message)

def display_agent_status():
    """Display the status of all agents"""
    if st.session_state.router:
        status = st.session_state.router.get_agent_status()
        
        st.sidebar.subheader("🤖 Agent Status")
        st.sidebar.write(f"**Active Agents:** {status['available_agents']}")
        
        for agent in status['registered_agents']:
            st.sidebar.write(f"✅ {agent.replace('_', ' ').title()}")
        
        # Show routing keywords
        if st.sidebar.expander("🔍 Routing Keywords"):
            for agent, keywords in status['routing_keywords'].items():
                st.sidebar.write(f"**{agent.replace('_', ' ').title()}:**")
                st.sidebar.write(f"_{', '.join(keywords[:5])}..._")

def display_response(response: dict):
    """Display agent response in the appropriate format"""
    agent_name = response.get("agent", "unknown")
    
    # Show which agent handled the query
    st.info(f"🤖 Handled by: **{agent_name.replace('_', ' ').title()} Agent**")
    
    # Display the main response
    st.write("**Response:**")
    st.write(response.get("response", "No response available"))
    
    # Handle different response types
    if agent_name == "sql":
        # SQL Agent - show query and results
        if "sql_query" in response and response["sql_query"]:
            st.subheader("📝 Generated SQL Query:")
            st.code(response["sql_query"], language="sql")
        
        if "data" in response and response["data"] is not None:
            st.subheader("📊 Query Results:")
            df = response["data"]
            if not df.empty:
                st.dataframe(df)
                st.write(f"*{len(df)} rows returned*")
            else:
                st.write("No results found.")
    
    elif agent_name == "web_search":
        # Web Search Agent - show sources
        if "sources" in response and response["sources"]:
            st.subheader("🔗 Sources:")
            for i, source in enumerate(response["sources"], 1):
                st.write(f"**{i}. {source.get('title', 'No title')}**")
                st.write(f"URL: {source.get('url', 'No URL')}")
                st.write(f"_{source.get('description', 'No description')}_")
                st.write("---")
    
    elif agent_name == "document":
        # Document Agent - show document sources
        if "sources" in response and response["sources"]:
            st.subheader("📚 Document Sources:")
            for i, source in enumerate(response["sources"], 1):
                st.write(f"**{i}. {source.get('filename', 'Unknown file')}**")
                st.write(f"_{source.get('content_preview', 'No preview')}_")
                if 'score' in source:
                    st.write(f"*Relevance: {source['score']:.3f}*")
                st.write("---")
    
    # Show errors if any
    if "error" in response:
        st.error(f"❌ Error: {response['error']}")

def display_conversation_history():
    """Display conversation history"""
    st.sidebar.subheader("💬 Conversation History")
    
    history = st.session_state.memory.get_recent_messages(10)
    
    if not history:
        st.sidebar.write("_No conversation history yet_")
        return
    
    # Show conversation stats
    stats = st.session_state.memory.get_stats()
    st.sidebar.write(f"**Total Messages:** {stats['total_messages']}")
    
    if stats['agent_usage']:
        st.sidebar.write("**Agent Usage:**")
        for agent, count in stats['agent_usage'].items():
            st.sidebar.write(f"- {agent.replace('_', ' ').title()}: {count}")
    
    # Show recent messages
    if st.sidebar.expander("Recent Messages", expanded=False):
        for msg in reversed(history[-6:]):  # Show last 6 messages
            role_icon = "🧑" if msg["role"] == "user" else "🤖"
            time_str = msg["timestamp"].split("T")[1][:8]  # Just time part
            st.sidebar.write(f"{role_icon} **{time_str}**")
            st.sidebar.write(f"_{msg['content'][:100]}..._")
            st.sidebar.write("---")

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Multi-Agent Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🤖 Multi-Agent Chatbot")
    st.subheader("Powered by Web Search, SQL Database, and Document Analysis")
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize agents if not already done
    if not st.session_state.agents_initialized:
        if st.button("🚀 Initialize Agents"):
            initialize_agents()
    
    # Show error if initialization failed
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.stop()
    
    # Display agent status and conversation history in sidebar
    display_agent_status()
    display_conversation_history()
    
    # Main chat interface
    if st.session_state.agents_initialized and st.session_state.router:
        st.write("---")
        st.subheader("💬 Chat Interface")
        
        # Chat input
        user_input = st.text_input(
            "Ask me anything about current events, database queries, or document analysis:",
            placeholder="e.g., What's the weather today? How many customers do we have? Explain the document concepts..."
        )
        
        col1, col2, col3 = st.columns([1, 1, 8])
        
        with col1:
            send_button = st.button("📤 Send")
        
        with col2:
            clear_button = st.button("🗑️ Clear Chat")
        
        if clear_button:
            st.session_state.memory.clear()
            st.rerun()
        
        # Process user input
        if send_button and user_input.strip():
            # Add user message to memory
            st.session_state.memory.add_message("user", user_input)
            
            # Show routing explanation
            routing_info = st.session_state.router.explain_routing(user_input)
            st.info(f"🎯 Routing to: **{routing_info['selected_agent'].replace('_', ' ').title()}** Agent")
            
            # Process query
            with st.spinner("Processing your query..."):
                response = st.session_state.router.process_query(user_input)
            
            # Display response
            display_response(response)
            
            # Add assistant response to memory
            st.session_state.memory.add_message(
                "assistant", 
                response.get("response", "No response"), 
                response
            )
            
            # Clear input
            st.rerun()
    
    else:
        st.warning("⚠️ Please initialize the agents first by clicking the 'Initialize Agents' button above.")
        
        # Show sample queries
        st.subheader("📝 Sample Queries")
        st.write("Here are some example queries you can try once the agents are initialized:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🌐 Web Search Examples:**")
            st.write("- What's the weather today?")
            st.write("- Latest tech news")
            st.write("- Bitcoin price today")
            st.write("- Current events")
        
        with col2:
            st.write("**🗄️ Database Examples:**")
            st.write("- How many customers do we have?")
            st.write("- Show me sales data")
            st.write("- Total revenue this month")
            st.write("- List all products")
        
        with col3:
            st.write("**📄 Document Examples:**")
            st.write("- Summarize the documents")
            st.write("- Explain the key concepts")
            st.write("- What are the main topics?")
            st.write("- Tell me about the content")

if __name__ == "__main__":
    main()
