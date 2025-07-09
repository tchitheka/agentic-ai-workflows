# Multi-Agent Chatbot

A simple but powerful Streamlit-based chatbot powered by multiple specialized AI agents that can handle web search, database queries, and document analysis.

## Features

- **🌐 Web Search Agent**: Real-time web search using Brave Search API
- **🗄️ SQL Agent**: Natural language to SQL conversion and database querying
- **📄 Document Agent**: Document analysis and Q&A using LlamaIndex RAG
- **🤖 Router Agent**: Intelligent routing of queries to the appropriate agent
- **💬 Conversation Memory**: Maintains conversation history and context
- **🎯 Smart Routing**: Keyword-based routing with fallback logic

## Architecture

```
multi_agent_chatbot/
├── app.py                 # Main Streamlit application
├── agents/
│   ├── router_agent.py    # Routes queries to appropriate agents
│   ├── web_search_agent.py # Handles web search queries
│   ├── sql_agent.py       # Handles database queries
│   └── document_agent.py  # Handles document analysis
├── config/
│   └── settings.py        # Configuration management
├── utils/
│   └── memory.py          # Conversation memory system
└── data/
    ├── sample_database.sqlite # Sample e-commerce database
    └── documents/         # Document storage directory
```

## Setup

### 1. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_VERSION=2024-02-01
AZURE_OPENAI_MODEL=gpt-4

# Azure OpenAI Embeddings Configuration
EMBEDDINGS_API_KEY=your_embeddings_api_key
EMBEDDINGS_API_ENDPOINT=your_embeddings_endpoint
EMBEDDINGS_DEPLOYMENT_NAME=your_embeddings_deployment
EMBEDDINGS_API_VERSION=2024-02-01
EMBEDDINGS_MODEL=text-embedding-3-small

# Brave Search Configuration
BRAVE_SEARCH_API_KEY=your_brave_search_api_key
```

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

## Usage

### Starting the Application

1. Run `streamlit run app.py`
2. Click "🚀 Initialize Agents" to set up all agents
3. Start chatting with the multi-agent system

### Query Examples

#### Web Search Queries
- "What's the weather today?"
- "Latest tech news"
- "Bitcoin price today"
- "Current events in AI"

#### Database Queries
- "How many customers do we have?"
- "Show me sales data"
- "Total revenue this month"
- "List all products"

#### Document Queries
- "Summarize the documents"
- "Explain the key concepts"
- "What are the main topics?"
- "Tell me about the content"

## Agent Details

### Router Agent
- **Purpose**: Determines which agent should handle each query
- **Routing Logic**: Keyword-based matching with fallback logic
- **Keywords**: 
  - Web Search: "current", "latest", "news", "weather", "price"
  - SQL: "data", "customers", "orders", "count", "total"
  - Document: "document", "explain", "summary", "concept"

### Web Search Agent
- **API**: Brave Search API
- **Capabilities**: Real-time web search, source citation
- **Safety**: Read-only web access
- **Output**: Formatted response with source links

### SQL Agent
- **Database**: SQLite with e-commerce sample data
- **Safety**: Only SELECT queries allowed
- **Tables**: customers, orders, products, order_items, reviews
- **Output**: SQL query + results table

### Document Agent
- **Technology**: LlamaIndex RAG with Azure OpenAI embeddings
- **Capabilities**: Document analysis, semantic search, Q&A
- **Memory**: Conversational context maintenance
- **Output**: Analysis with source document citations

## Database Schema

The sample database includes:

- **customers**: Customer information
- **products**: Product catalog
- **orders**: Order records
- **order_items**: Order line items
- **reviews**: Product reviews

## Document Support

The document agent supports:
- Text files (.txt)
- PDF files (.pdf)
- Word documents (.docx)
- Markdown files (.md)

Place documents in the `data/documents/` directory.

## Memory System

- **Capacity**: Stores up to 50 messages
- **Features**: Conversation history, agent usage statistics
- **Context**: Provides recent conversation context to agents

## Configuration

All configuration is managed through `config/settings.py`:

- API keys and endpoints
- Database paths
- Document directories
- Agent parameters

## Error Handling

- **Graceful Degradation**: If an agent fails, others continue working
- **User-Friendly Messages**: Clear error messages for users
- **Logging**: Error logging for debugging

## Customization

### Adding New Agents

1. Create agent class in `agents/` directory
2. Implement `process_query()` method
3. Register agent with router
4. Add routing keywords

### Modifying Routing Logic

Edit `agents/router_agent.py`:
- Add new keywords to `routing_keywords`
- Modify `route_query()` method
- Update fallback logic

### Extending Memory

Edit `utils/memory.py`:
- Add new metadata fields
- Implement search functionality
- Add persistence if needed

## Troubleshooting

### Common Issues

1. **Agent initialization fails**
   - Check API keys in `.env` file
   - Verify endpoint URLs
   - Ensure all dependencies are installed

2. **Database queries fail**
   - Verify `sample_database.sqlite` exists
   - Check file permissions
   - Validate SQL query syntax

3. **Document queries fail**
   - Ensure documents exist in `data/documents/`
   - Check file formats are supported
   - Verify embeddings API configuration

### Performance Tips

- Keep document directory small for faster indexing
- Use specific queries for better routing
- Clear conversation history periodically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes and learning about multi-agent AI systems.
