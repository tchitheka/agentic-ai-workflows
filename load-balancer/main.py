from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from azure_openai_load_balancer import AzureOpenAILoadBalancer
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Azure OpenAI Load Balancer", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
AZURE_OPENAI_BASE_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_KEY")
API_VERSION = os.getenv("AZURE_OPENAI_VERSION")  # Default to a common API version
DEPLOYMENTS = ["gpt-4o-mini", "gpt-4o-mini-v2"]  # your Azure deployment names

# Validate environment variables
if not AZURE_OPENAI_BASE_URL or not AZURE_API_KEY:
    raise ValueError("AZURE_OPENAI_BASE_URL and AZURE_API_KEY environment variables are required")

load_balancer = AzureOpenAILoadBalancer(
    base_url=AZURE_OPENAI_BASE_URL,
    api_key=AZURE_API_KEY,
    deployment_names=DEPLOYMENTS,
    api_version=API_VERSION
)

@app.get("/")
async def root():
    return {"message": "Azure OpenAI Load Balancer is running", "deployments": DEPLOYMENTS}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(datetime.now())}

@app.post("/chat")
async def chat(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Received chat request with {len(payload.get('messages', []))} messages")
        response = await load_balancer.forward_request(payload)
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# For compatibility with OpenAI SDK format
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    return await chat(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)