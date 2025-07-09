#!/bin/bash

# Simple Multi-Agent Chatbot Runner
# This script helps you run the chatbot in different modes

echo "🤖 Simple Multi-Agent Chatbot Runner"
echo "===================================="
echo

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d "../venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing requirements..."
    pip install -r requirements.txt
else
    echo "✅ Virtual environment found"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source ../venv/bin/activate
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ] && [ ! -f "../.env" ]; then
    echo "❌ .env file not found. Please create one with your API keys."
    exit 1
fi

echo "✅ Environment configured"
echo

# Show options
echo "Choose how to run the chatbot:"
echo "1. Command Line Interface (simple)"
echo "2. Streamlit Web Interface (recommended)"
echo "3. Original Streamlit App (complex)"
echo "4. Demo Script"
echo

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting Command Line Interface..."
        python simple_agent.py
        ;;
    2)
        echo "🚀 Starting Simple Streamlit App..."
        echo "📱 Opening browser at http://localhost:8501"
        streamlit run simple_app.py
        ;;
    3)
        echo "🚀 Starting Original Streamlit App..."
        echo "📱 Opening browser at http://localhost:8501"
        streamlit run app.py
        ;;
    4)
        echo "🚀 Running Demo Script..."
        python demo.py
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        ;;
esac
