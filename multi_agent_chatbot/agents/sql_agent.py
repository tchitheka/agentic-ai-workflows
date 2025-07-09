"""
SQL Agent - Handles database queries by converting natural language to SQL
"""
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional
from openai import AzureOpenAI

class SQLAgent:
    def __init__(self, db_path: str, openai_client: AzureOpenAI, model: str):
        """
        Initialize the SQL Agent
        
        Args:
            db_path: Path to the SQLite database
            openai_client: Azure OpenAI client
            model: Model name to use
        """
        self.db_path = db_path
        self.client = openai_client
        self.model = model
        self.agent_name = "sql"
        self.schema_info = None
        self._load_schema()
    
    def _load_schema(self):
        """Load database schema information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                schema_info = {}
                for table in tables:
                    table_name = table[0]
                    
                    # Get column info
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    schema_info[table_name] = {
                        "columns": columns,
                        "sample_data": self._get_sample_data(cursor, table_name)
                    }
                
                self.schema_info = schema_info
                
        except Exception as e:
            print(f"Error loading schema: {e}")
            self.schema_info = {}
    
    def _get_sample_data(self, cursor, table_name: str, limit: int = 3):
        """Get sample data from a table"""
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            return cursor.fetchall()
        except Exception:
            return []
    
    def get_schema_description(self) -> str:
        """Get a readable description of the database schema"""
        if not self.schema_info:
            return "Database schema not available."
        
        schema_desc = "Database Schema:\n\n"
        
        for table_name, table_info in self.schema_info.items():
            schema_desc += f"Table: {table_name}\n"
            schema_desc += "Columns:\n"
            
            for col in table_info["columns"]:
                col_name = col[1]
                col_type = col[2]
                is_nullable = "NULL" if col[3] == 0 else "NOT NULL"
                is_pk = " (PRIMARY KEY)" if col[5] == 1 else ""
                schema_desc += f"  - {col_name}: {col_type} {is_nullable}{is_pk}\n"
            
            # Add sample data
            if table_info["sample_data"]:
                schema_desc += f"Sample data:\n"
                for row in table_info["sample_data"][:2]:  # Show first 2 rows
                    schema_desc += f"  {row}\n"
            
            schema_desc += "\n"
        
        return schema_desc
    
    def text_to_sql(self, query: str) -> str:
        """
        Convert natural language query to SQL
        
        Args:
            query: Natural language query
            
        Returns:
            SQL query string
        """
        schema_desc = self.get_schema_description()
        
        prompt = f"""
        You are a SQL expert. Convert the following natural language query to a SQL query based on the database schema provided.

        DATABASE SCHEMA:
        {schema_desc}

        NATURAL LANGUAGE QUERY: {query}

        INSTRUCTIONS:
        1. Write a valid SQL query that answers the question
        2. Use appropriate table joins if needed
        3. Include proper WHERE clauses for filtering
        4. Use appropriate aggregate functions (COUNT, SUM, AVG, etc.) when needed
        5. Return ONLY the SQL query, no explanations
        6. Make sure column names and table names match exactly what's in the schema

        SQL QUERY:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a SQL expert. Convert natural language to SQL queries. Return only valid SQL."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=400
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query (remove markdown formatting if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()
            
            return sql_query
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query safely
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Dictionary with results or error information
        """
        try:
            # Basic safety checks
            sql_lower = sql_query.lower().strip()
            
            # Only allow SELECT queries for safety
            if not sql_lower.startswith('select'):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed for safety reasons.",
                    "data": None
                }
            
            # Prevent potentially dangerous operations
            dangerous_keywords = ['drop', 'delete', 'update', 'insert', 'alter', 'create']
            if any(keyword in sql_lower for keyword in dangerous_keywords):
                return {
                    "success": False,
                    "error": "Query contains potentially dangerous operations.",
                    "data": None
                }
            
            # Execute query
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(sql_query, conn)
                
                return {
                    "success": True,
                    "data": df,
                    "row_count": len(df),
                    "columns": df.columns.tolist()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language database query
        
        Args:
            query: User's natural language query
            
        Returns:
            Response dictionary with query results
        """
        try:
            # Convert to SQL
            sql_query = self.text_to_sql(query)
            
            if sql_query.startswith("Error"):
                return {
                    "response": f"I couldn't convert your query to SQL: {sql_query}",
                    "agent": self.agent_name,
                    "error": sql_query,
                    "sql_query": None,
                    "data": None
                }
            
            # Execute SQL
            result = self.execute_sql(sql_query)
            
            if not result["success"]:
                return {
                    "response": f"Error executing query: {result['error']}",
                    "agent": self.agent_name,
                    "error": result['error'],
                    "sql_query": sql_query,
                    "data": None
                }
            
            # Format response
            df = result["data"]
            row_count = result["row_count"]
            
            if row_count == 0:
                response_text = "No results found for your query."
            else:
                response_text = f"Found {row_count} result(s) for your query."
            
            return {
                "response": response_text,
                "agent": self.agent_name,
                "sql_query": sql_query,
                "data": df,
                "row_count": row_count,
                "columns": result["columns"]
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error while processing your database query: {str(e)}",
                "agent": self.agent_name,
                "error": str(e),
                "sql_query": None,
                "data": None
            }
    
    def test_connection(self) -> bool:
        """
        Test if database connection is working
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table information
        """
        if not self.schema_info or table_name not in self.schema_info:
            return {"error": f"Table {table_name} not found"}
        
        table_info = self.schema_info[table_name]
        return {
            "table_name": table_name,
            "columns": table_info["columns"],
            "sample_data": table_info["sample_data"]
        }
