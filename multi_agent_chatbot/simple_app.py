#!/usr/bin/env python3
"""
Simple Multi-Agent Chatbot - Streamlit version
A clean, modern chatbot interface for multi-agent conversations
"""
import streamlit as st
import sys
import os
from typing import Dict, Any
import json
import time
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from openai import AzureOpenAI
import requests
import sqlite3
import glob

@st.cache_resource
def init_agent():
    """Initialize the agent (cached for performance)"""
    return SimpleStreamlitAgent()

class SimpleStreamlitAgent:
    def __init__(self):
        """Initialize the simple agent"""
        self.setup_openai_client()
        self.setup_database()
        self.setup_documents()
        
    def setup_openai_client(self):
        """Setup Azure OpenAI client"""
        try:
            self.client = AzureOpenAI(
                api_key=settings.openai_key,
                azure_endpoint=settings.openai_endpoint,
                api_version=settings.openai_api_version,
            )
            return True
        except Exception as e:
            st.error(f"OpenAI client setup failed: {e}")
            self.client = None
            return False
    
    def setup_database(self):
        """Setup database connection"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), settings.database_path)
            if os.path.exists(db_path):
                self.db_path = db_path
                return True
            else:
                self.db_path = None
                return False
        except Exception as e:
            st.error(f"Database setup failed: {e}")
            self.db_path = None
            return False
    
    def setup_documents(self):
        """Setup document processing"""
        try:
            docs_path = os.path.join(os.path.dirname(__file__), settings.documents_path)
            if os.path.exists(docs_path):
                self.docs_path = docs_path
                return True
            else:
                self.docs_path = None
                return False
        except Exception as e:
            st.error(f"Documents setup failed: {e}")
            self.docs_path = None
            return False
    
    def determine_intent(self, query: str) -> str:
        """Determine what type of query this is"""
        query_lower = query.lower()
        
        # Database keywords
        db_keywords = ["data", "database", "customers", "orders", "products", "sales", 
                      "count", "total", "sum", "average", "revenue", "how many", "show me", "list"]
        
        # Web search keywords
        web_keywords = ["current", "latest", "recent", "today", "now", "news", "weather", 
                       "price", "stock", "trending", "happening", "update", "bitcoin", "crypto"]
        
        # Document keywords
        doc_keywords = ["document", "documents", "explain", "definition", "concept", 
                       "summary", "summarize", "analyze", "what is", "tell me about", "describe"]
        
        # Count matches
        db_score = sum(1 for keyword in db_keywords if keyword in query_lower)
        web_score = sum(1 for keyword in web_keywords if keyword in query_lower)
        doc_score = sum(1 for keyword in doc_keywords if keyword in query_lower)
        
        # Return highest scoring intent
        if db_score > web_score and db_score > doc_score:
            return "database"
        elif web_score > doc_score:
            return "web_search"
        else:
            return "document"
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """Search the web using Brave Search API"""
        if not settings.brave_search_key:
            return {"error": "Brave Search API key not configured"}
        
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            response = requests.get(
                url,
                headers={"X-Subscription-Token": settings.brave_search_key},
                params={"q": query, "count": 3, "country": "us", "search_lang": "en"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Search API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def query_database(self, query: str) -> Dict[str, Any]:
        """Query the database"""
        if not self.db_path:
            return {"error": "Database not available"}
        
        try:
            # Generate SQL query using AI
            sql_prompt = f"""
            Generate a SQL query to answer this question: {query}
            
            Available tables and their columns:
            - customers: customer_id, name, email, phone, address, city, state, zip_code, country, created_at
            - products: product_id, name, description, price, category, stock_quantity, created_at
            - orders: order_id, customer_id, order_date, total_amount, status, shipping_address
            - order_items: order_item_id, order_id, product_id, quantity, price
            - reviews: review_id, customer_id, product_id, rating, comment, created_at
            
            Return only the SQL query, no explanation.
            """
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only valid SQL queries."},
                    {"role": "user", "content": sql_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Execute the query
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return {
                    "sql_query": sql_query,
                    "results": results,
                    "columns": columns
                }
                
        except Exception as e:
            return {"error": f"Database query failed: {str(e)}"}
    
    def analyze_documents(self, query: str) -> Dict[str, Any]:
        """Analyze documents"""
        if not self.docs_path:
            return {"error": "Documents not available"}
        
        try:
            # Read all text files
            documents = []
            for file_path in glob.glob(os.path.join(self.docs_path, "*.txt")):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        "filename": os.path.basename(file_path),
                        "content": content[:2000]  # Limit content length
                    })
            
            if not documents:
                return {"error": "No documents found"}
            
            # Combine document content
            combined_content = "\\n\\n".join([f"Document: {doc['filename']}\\n{doc['content']}" for doc in documents])
            
            # Generate response
            doc_prompt = f"""
            Based on the following documents, please answer this question: {query}
            
            Documents:
            {combined_content}
            
            Please provide a helpful answer based on the document content.
            """
            
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes documents."},
                    {"role": "user", "content": doc_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            return {
                "response": response.choices[0].message.content,
                "documents": documents
            }
            
        except Exception as e:
            return {"error": f"Document analysis failed: {str(e)}"}
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query and return response"""
        if not self.client:
            return {"error": "OpenAI client not available. Please check your configuration."}
        
        # Determine intent
        intent = self.determine_intent(query)
        
        try:
            if intent == "web_search":
                search_data = self.search_web(query)
                if "error" in search_data:
                    return {"error": f"Web search error: {search_data['error']}", "intent": intent}
                
                # Generate response from web search
                results = search_data.get('web', {}).get('results', [])
                if not results:
                    return {"response": "No web search results found.", "intent": intent}
                
                # Format results for AI
                formatted_results = []
                sources = []
                for i, result in enumerate(results[:3]):
                    title = result.get('title', 'No title')
                    description = result.get('description', 'No description')
                    url = result.get('url', 'No URL')
                    formatted_results.append(f"[{i+1}] {title}\\n{description}\\nURL: {url}")
                    sources.append({"title": title, "url": url, "description": description})
                
                search_context = "\\n\\n".join(formatted_results)
                
                # Generate response
                prompt = f"""
                Based on these web search results, answer the question: {query}
                
                Search Results:
                {search_context}
                
                Provide a helpful answer based on the search results.
                """
                
                response = self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on web search results."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    "response": response.choices[0].message.content,
                    "intent": intent,
                    "sources": sources
                }
                
            elif intent == "database":
                db_data = self.query_database(query)
                if "error" in db_data:
                    return {"error": f"Database error: {db_data['error']}", "intent": intent}
                
                sql_query = db_data.get('sql_query', '')
                results = db_data.get('results', [])
                columns = db_data.get('columns', [])
                
                if not results:
                    return {"response": f"No results found for your query.\\nSQL Query used: {sql_query}", "intent": intent, "sql_query": sql_query}
                
                return {
                    "response": f"Found {len(results)} results.",
                    "intent": intent,
                    "sql_query": sql_query,
                    "results": results,
                    "columns": columns
                }
                
            elif intent == "document":
                doc_data = self.analyze_documents(query)
                if "error" in doc_data:
                    return {"error": f"Document analysis error: {doc_data['error']}", "intent": intent}
                
                return {
                    "response": doc_data['response'],
                    "intent": intent,
                    "documents": doc_data['documents']
                }
            
            else:
                return {"response": "I'm not sure how to handle that query. Please try rephrasing.", "intent": intent}
            
        except Exception as e:
            return {"error": f"Error processing query: {str(e)}", "intent": intent}

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="Simple Multi-Agent Chatbot",
        page_icon="🤖",
        layout="centered"  # Changed from "wide" to "centered"
    )
    
    # Add custom CSS to improve chat appearance
    st.markdown("""
    <style>
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    .stChatMessage {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    .stChatFloatingInputContainer {
        max-width: 800px;
        margin: 0 auto;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>🤖 AI Chatbot</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Check configuration
    try:
        settings.validate_config()
        # Move validation confirmation to a smaller, less intrusive notification
        st.toast("✅ System ready", icon="✅")
    except Exception as e:
        st.error(f"❌ Configuration error: {e}")
        st.stop()
    
    # Initialize agent
    agent = init_agent()
    
    # Create a clean container for the chat interface
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message if chat is empty
        if not st.session_state.messages:
            st.markdown("""
            <div class="info-box">
            <p>👋 Hi there! I'm your multi-agent assistant. I can help with:</p>
            <ul>
                <li>🌐 <strong>Web searches</strong> - Current events, news, prices</li>
                <li>🗄️ <strong>Database queries</strong> - Find information in your database</li>
                <li>📄 <strong>Document analysis</strong> - Understand documents and answer questions</li>
            </ul>
            <p>What can I help you with today?</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = agent.process_query(prompt)
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                response_text = result['error']
            else:
                intent = result.get('intent', 'unknown')
                # Make intent indicator more subtle
                response_text = result['response']
                
                # Create a clean response with proper formatting
                st.markdown(response_text)
                
                # Display additional information in collapsible sections when appropriate
                if intent == "web_search" and "sources" in result:
                    with st.expander("Sources"):
                        for i, source in enumerate(result['sources'], 1):
                            st.markdown(f"{i}. [{source['title']}]({source['url']})")
                            st.markdown(f"   _{source['description'][:100]}..._")
                
                elif intent == "database" and "results" in result:
                    with st.expander("Database Results"):
                        if result['results']:
                            import pandas as pd
                            df = pd.DataFrame(result['results'], columns=result['columns'])
                            st.dataframe(df, use_container_width=True)
                        st.markdown("**Query Used:**")
                        st.code(result['sql_query'], language='sql')
                
                elif intent == "document" and "documents" in result:
                    with st.expander("Document Sources"):
                        for doc in result['documents']:
                            st.markdown(f"- {doc['filename']}")
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    # Footer with a cleaner clear chat button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Show examples in the footer instead of at the top
    with st.expander("💡 Example queries"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Web Search**")
            st.markdown("- What's the weather today?")
            st.markdown("- Bitcoin price now")
            st.markdown("- Latest AI news")
        with col2:
            st.markdown("**Database**")
            st.markdown("- How many customers?")
            st.markdown("- Show me all products")
            st.markdown("- Total sales revenue")
        with col3:
            st.markdown("**Documents**")
            st.markdown("- Summarize documents")
            st.markdown("- Explain the concepts")
            st.markdown("- What are the main topics?")

if __name__ == "__main__":
    main()
