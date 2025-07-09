"""
Document Agent - Handles document-based queries using LlamaIndex RAG
"""
import os
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.azure_openai import AzureOpenAI as LlamaAzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

class DocumentAgent:
    def __init__(self, documents_path: str, openai_client: AzureOpenAI, model: str, 
                 embeddings_config: Dict[str, str], openai_config: Dict[str, str]):
        """
        Initialize the Document Agent
        
        Args:
            documents_path: Path to documents directory
            openai_client: Azure OpenAI client
            model: Model name to use
            embeddings_config: Embeddings configuration
            openai_config: OpenAI configuration
        """
        self.documents_path = documents_path
        self.client = openai_client
        self.model = model
        self.agent_name = "document"
        self.index = None
        self.query_engine = None
        self.chat_engine = None
        
        # Configure LlamaIndex settings
        self._configure_llamaindex(embeddings_config, openai_config)
        
        # Load documents and create index
        self._load_documents()
    
    def _configure_llamaindex(self, embeddings_config: Dict[str, str], openai_config: Dict[str, str]):
        """Configure LlamaIndex with Azure OpenAI"""
        try:
            # Set environment variable that LlamaIndex expects
            os.environ["AZURE_OPENAI_API_KEY"] = openai_config.get("api_key", "")
            
            # Set up LLM
            llm = LlamaAzureOpenAI(
                model=openai_config.get("model", "gpt-4"),
                deployment_name=openai_config.get("azure_deployment"),
                api_key=openai_config.get("api_key"),
                azure_endpoint=openai_config.get("azure_endpoint"),
                api_version=openai_config.get("api_version"),
                temperature=0.1,
            )
            
            # Set up embedding model
            embed_model = AzureOpenAIEmbedding(
                model=embeddings_config.get("model", "text-embedding-3-small"),
                deployment_name=embeddings_config.get("azure_deployment"),
                api_key=embeddings_config.get("api_key"),
                azure_endpoint=embeddings_config.get("azure_endpoint"),
                api_version=embeddings_config.get("api_version"),
            )
            
            # Configure global settings
            Settings.llm = llm
            Settings.embed_model = embed_model
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 200
            
        except Exception as e:
            print(f"Error configuring LlamaIndex: {e}")
            raise
    
    def _load_documents(self):
        """Load documents and create vector index"""
        try:
            if not os.path.exists(self.documents_path):
                print(f"Documents directory not found: {self.documents_path}")
                return
            
            # Check if there are any documents
            if not os.listdir(self.documents_path):
                print(f"No documents found in {self.documents_path}")
                return
            
            # Load documents
            documents = SimpleDirectoryReader(
                input_dir=self.documents_path,
                recursive=True
            ).load_data()
            
            if not documents:
                print("No documents were loaded")
                return
            
            # Create vector index
            self.index = VectorStoreIndex.from_documents(documents)
            
            # Create query engine
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=3,
                response_mode="tree_summarize"
            )
            
            # Create chat engine for conversational queries
            memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
            self.chat_engine = self.index.as_chat_engine(
                chat_mode="context",
                memory=memory,
                similarity_top_k=3,
                system_prompt=(
                    "You are a helpful document analysis assistant. "
                    "Answer questions based on the provided document content. "
                    "Always cite the source document when possible. "
                    "If information is not in the documents, clearly state that."
                )
            )
            
            print(f"✅ Loaded {len(documents)} documents and created index")
            
        except Exception as e:
            print(f"Error loading documents: {e}")
            self.index = None
            self.query_engine = None
            self.chat_engine = None
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get information about loaded documents"""
        if not self.index:
            return {"error": "No documents loaded"}
        
        try:
            # Get document metadata
            doc_info = []
            for doc_id, doc in self.index.docstore.docs.items():
                doc_info.append({
                    "id": doc_id,
                    "filename": doc.metadata.get("file_name", "Unknown"),
                    "content_length": len(doc.text),
                    "content_preview": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
                })
            
            return {
                "document_count": len(doc_info),
                "documents": doc_info
            }
            
        except Exception as e:
            return {"error": f"Error getting document info: {str(e)}"}
    
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant document chunks
        """
        if not self.index:
            return []
        
        try:
            # Get retriever
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            
            # Retrieve relevant nodes
            nodes = retriever.retrieve(query)
            
            results = []
            for node in nodes:
                results.append({
                    "text": node.text,
                    "score": getattr(node, 'score', 0.0),
                    "metadata": node.metadata,
                    "filename": node.metadata.get("file_name", "Unknown")
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a document-based query
        
        Args:
            query: User's query about documents
            
        Returns:
            Response dictionary with document analysis results
        """
        if not self.index or not self.query_engine:
            return {
                "response": "Sorry, no documents are currently loaded. Please add documents to the documents directory.",
                "agent": self.agent_name,
                "error": "No documents loaded",
                "sources": []
            }
        
        try:
            # Query the documents
            response = self.query_engine.query(query)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    sources.append({
                        "filename": node.metadata.get("file_name", "Unknown"),
                        "content_preview": node.text[:150] + "..." if len(node.text) > 150 else node.text,
                        "score": getattr(node, 'score', 0.0)
                    })
            
            return {
                "response": str(response.response),
                "agent": self.agent_name,
                "sources": sources,
                "query": query,
                "source_count": len(sources)
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error while analyzing the documents: {str(e)}",
                "agent": self.agent_name,
                "error": str(e),
                "sources": []
            }
    
    def ask_conversational(self, query: str) -> Dict[str, Any]:
        """
        Ask a conversational question that maintains context
        
        Args:
            query: User's conversational query
            
        Returns:
            Response dictionary with conversational response
        """
        if not self.chat_engine:
            return self.process_query(query)  # Fallback to regular query
        
        try:
            response = self.chat_engine.chat(query)
            
            # Extract source information
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    sources.append({
                        "filename": node.metadata.get("file_name", "Unknown"),
                        "content_preview": node.text[:150] + "..." if len(node.text) > 150 else node.text,
                        "score": getattr(node, 'score', 0.0)
                    })
            
            return {
                "response": str(response.response),
                "agent": self.agent_name,
                "sources": sources,
                "query": query,
                "conversational": True
            }
            
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error in the conversational query: {str(e)}",
                "agent": self.agent_name,
                "error": str(e),
                "sources": []
            }
    
    def summarize_documents(self) -> Dict[str, Any]:
        """
        Generate a summary of all documents
        
        Returns:
            Response dictionary with document summary
        """
        if not self.query_engine:
            return {
                "response": "No documents available to summarize.",
                "agent": self.agent_name,
                "error": "No documents loaded"
            }
        
        summary_query = """
        Provide a comprehensive summary of all the documents. Include:
        1. Main topics covered
        2. Key concepts and insights
        3. Important information from each document
        Structure your response clearly with headers.
        """
        
        return self.process_query(summary_query)
    
    def test_connection(self) -> bool:
        """
        Test if document processing is working
        
        Returns:
            True if working, False otherwise
        """
        try:
            return self.index is not None and self.query_engine is not None
        except Exception:
            return False
