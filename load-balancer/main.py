from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from azure_openai_load_balancer import AzureOpenAILoadBalancer
from dotenv import load_dotenv, find_dotenv
import os
import logging

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Azure OpenAI Load Balancer for Students", version="1.0.0")

# Add CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚙️ Set your Azure config here or via environment variables
AZURE_OPENAI_BASE_URL = os.environ.get("AZURE_OPENAI_ENDPOINT")  # e.g., https://<resource>.openai.azure.com
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_KEY")
API_VERSION = os.environ.get("AZURE_OPENAI_VERSION", "2024-12-01-preview")  # Default API version

# Multiple deployments for load balancing - add more as needed
DEPLOYMENTS = [
    os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),  # Primary deployment
]

# Check for additional deployments in environment variables
additional_deployments = [
    os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME_V2"),  # Second deployment
    os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME_V3"),  # Third deployment
    os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME_V4"),  # Fourth deployment
]

# Add any additional deployments that exist
for deployment in additional_deployments:
    if deployment:
        DEPLOYMENTS.append(deployment)

# Remove any None values from deployments
DEPLOYMENTS = [d for d in DEPLOYMENTS if d is not None]

logger.info(f"Initializing load balancer with {len(DEPLOYMENTS)} deployments: {DEPLOYMENTS}")

if len(DEPLOYMENTS) == 1:
    logger.warning("Only 1 deployment found. Consider adding more deployments to handle higher student load.")
else:
    logger.info(f"Load balancer ready with {len(DEPLOYMENTS)} deployments for student access.")

load_balancer = AzureOpenAILoadBalancer(
    base_url=AZURE_OPENAI_BASE_URL,
    api_key=AZURE_API_KEY,
    deployment_names=DEPLOYMENTS,
    api_version=API_VERSION
)

@app.get("/")
async def root():
    return {
        "message": "Azure OpenAI Load Balancer for Students", 
        "deployments": DEPLOYMENTS,
        "total_deployments": len(DEPLOYMENTS),
        "status": "running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "deployments": DEPLOYMENTS,
        "total_deployments": len(DEPLOYMENTS)
    }

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

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "deployments": DEPLOYMENTS,
        "total_deployments": len(DEPLOYMENTS)
    }

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