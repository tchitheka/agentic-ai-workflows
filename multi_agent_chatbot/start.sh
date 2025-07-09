#!/bin/bash
# Quick start script for the multi-agent chatbot

echo "🚀 Starting Multi-Agent Chatbot"
echo "================================"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the multi_agent_chatbot directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please copy and configure your environment variables"
    exit 1
fi

# Test configuration
echo "🔧 Testing configuration..."
python -c "from config.settings import settings; settings.validate_config(); print('✅ Configuration valid')" || {
    echo "❌ Configuration test failed"
    exit 1
}

# Launch Streamlit
echo "🌐 Launching Streamlit application..."
echo "The app will open in your browser automatically"
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app.py
