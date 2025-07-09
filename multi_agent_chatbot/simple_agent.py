#!/usr/bin/env python3
"""
Simple Multi-Agent Chatbot - Simplified version that works reliably
"""
import sys
import os
from typing import Dict, Any, Optional
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from openai import AzureOpenAI
import requests
import sqlite3
import glob

class SimpleAgent:
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
            print("✅ OpenAI client initialized")
        except Exception as e:
            print(f"❌ OpenAI client setup failed: {e}")
            self.client = None
    
    def setup_database(self):
        """Setup database connection"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), settings.database_path)
            if os.path.exists(db_path):
                self.db_path = db_path
                print("✅ Database found")
            else:
                print("⚠️ Database not found")
                self.db_path = None
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            self.db_path = None
    
    def setup_documents(self):
        """Setup document processing"""
        try:
            docs_path = os.path.join(os.path.dirname(__file__), settings.documents_path)
            if os.path.exists(docs_path):
                self.docs_path = docs_path
                print("✅ Documents folder found")
            else:
                print("⚠️ Documents folder not found")
                self.docs_path = None
        except Exception as e:
            print(f"❌ Documents setup failed: {e}")
            self.docs_path = None
    
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
    
    def generate_web_response(self, query: str, search_data: Dict[str, Any]) -> str:
        """Generate response from web search results"""
        if "error" in search_data:
            return f"Web search error: {search_data['error']}"
        
        try:
            # Extract search results
            results = search_data.get('web', {}).get('results', [])
            if not results:
                return "No web search results found."
            
            # Format results for AI
            formatted_results = []
            for i, result in enumerate(results[:3]):
                title = result.get('title', 'No title')
                description = result.get('description', 'No description')
                url = result.get('url', 'No URL')
                formatted_results.append(f"[{i+1}] {title}\\n{description}\\nURL: {url}")
            
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
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating web response: {str(e)}"
    
    def generate_database_response(self, query: str, db_data: Dict[str, Any]) -> str:
        """Generate response from database query results"""
        if "error" in db_data:
            return f"Database error: {db_data['error']}"
        
        try:
            sql_query = db_data.get('sql_query', '')
            results = db_data.get('results', [])
            columns = db_data.get('columns', [])
            
            if not results:
                return f"No results found for your query.\\nSQL Query used: {sql_query}"
            
            # Format results for display
            response_parts = []
            response_parts.append(f"Found {len(results)} results:")
            
            # Show first few results
            for i, row in enumerate(results[:5]):
                row_data = dict(zip(columns, row))
                response_parts.append(f"\\n{i+1}. {row_data}")
            
            if len(results) > 5:
                response_parts.append(f"\\n... and {len(results) - 5} more results")
            
            response_parts.append(f"\\nSQL Query used: {sql_query}")
            
            return "\\n".join(response_parts)
            
        except Exception as e:
            return f"Error generating database response: {str(e)}"
    
    def process_query(self, query: str) -> str:
        """Process a user query and return response"""
        if not self.client:
            return "❌ OpenAI client not available. Please check your configuration."
        
        print(f"\\n🤔 Processing query: {query}")
        
        # Determine intent
        intent = self.determine_intent(query)
        print(f"🎯 Intent: {intent}")
        
        try:
            if intent == "web_search":
                print("🌐 Searching the web...")
                search_data = self.search_web(query)
                response = self.generate_web_response(query, search_data)
                
            elif intent == "database":
                print("🗄️ Querying database...")
                db_data = self.query_database(query)
                response = self.generate_database_response(query, db_data)
                
            elif intent == "document":
                print("📄 Analyzing documents...")
                doc_data = self.analyze_documents(query)
                if "error" in doc_data:
                    response = f"Document analysis error: {doc_data['error']}"
                else:
                    response = doc_data['response']
            
            else:
                response = "I'm not sure how to handle that query. Please try rephrasing."
            
            return response
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

def main():
    """Main function for interactive chat"""
    print("🤖 Simple Multi-Agent Chatbot")
    print("=" * 50)
    
    # Check configuration
    try:
        settings.validate_config()
        print("✅ Configuration validated")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required keys are set.")
        return
    
    # Initialize agent
    agent = SimpleAgent()
    
    print("\\n💬 Chat Interface")
    print("Type 'quit' to exit")
    print("Examples:")
    print("- What's the weather today?")
    print("- How many customers do we have?")
    print("- Summarize the documents")
    print()
    
    while True:
        try:
            query = input("🧑 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            # Process query
            response = agent.process_query(query)
            print(f"\\n🤖 Assistant: {response}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\\n\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
