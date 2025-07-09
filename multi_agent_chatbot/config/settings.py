"""
Configuration management for multi-agent chatbot
"""
import os
from dotenv import load_dotenv, find_dotenv

class Settings:
    def __init__(self):
        """Initialize settings by loading environment variables"""
        load_dotenv(find_dotenv())
        self.load_env_variables()
    
    def load_env_variables(self):
        """Load all necessary API keys and configurations"""
        # Azure OpenAI Configuration
        self.openai_key = os.getenv("AZURE_OPENAI_KEY")
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.openai_api_version = os.getenv("AZURE_OPENAI_VERSION")
        self.openai_model = os.getenv("AZURE_OPENAI_MODEL")
        
        # Azure OpenAI Embeddings Configuration
        self.embeddings_key = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_KEY")
        self.embeddings_endpoint = os.getenv("AZURE_OPENAI_EMBEDDINGS_ENDPOINT")
        self.embeddings_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME")
        self.embeddings_api_version = os.getenv("AZURE_OPENAI_EMBEDDINGS_API_VERSION")
        self.embeddings_model = os.getenv("AZURE_OPENAI_EMBEDDINGS_MODEL")
        
        # Brave Search Configuration
        self.brave_search_key = os.getenv("BRAVE_SEARCH_API_KEY")
        
        # Database Configuration
        self.database_path = "data/sample_database.sqlite"
        
        # Documents Configuration
        self.documents_path = "data/documents"
    
    def validate_config(self):
        """Validate that all required configuration is present"""
        required_configs = {
            "Azure OpenAI Key": self.openai_key,
            "Azure OpenAI Endpoint": self.openai_endpoint,
            "Azure OpenAI Deployment": self.openai_deployment,
            "Brave Search Key": self.brave_search_key,
        }
        
        missing_configs = []
        for name, value in required_configs.items():
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        return True
    
    def get_openai_client_config(self):
        """Get configuration for OpenAI client"""
        return {
            "api_key": self.openai_key,
            "azure_endpoint": self.openai_endpoint,
            "azure_deployment": self.openai_deployment,
            "api_version": self.openai_api_version,
            "model": self.openai_model
        }
    
    def get_embeddings_client_config(self):
        """Get configuration for embeddings client"""
        return {
            "api_key": self.embeddings_key,
            "azure_endpoint": self.embeddings_endpoint,
            "azure_deployment": self.embeddings_deployment,
            "api_version": self.embeddings_api_version,
            "model": self.embeddings_model
        }

# Global settings instance
settings = Settings()
