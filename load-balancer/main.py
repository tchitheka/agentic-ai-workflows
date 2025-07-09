from fastapi import FastAPI, Request, HTTPException
from azure_openai_load_balancer import AzureOpenAILoadBalancer
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())

app = FastAPI()

# ⚙️ Set your Azure config here or via environment variables
AZURE_OPENAI_BASE_URL = os.environ.get("AZURE_OPENAI_ENDPOINT")  # e.g., https://<resource>.openai.azure.com
AZURE_API_KEY = os.environ.get("AZURE_OPENAI_KEY")
API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")  # Default API version
DEPLOYMENTS = ["gpt-4o-mini", "gpt-4o-mini-v2"]

load_balancer = AzureOpenAILoadBalancer(
    base_url=AZURE_OPENAI_BASE_URL,
    api_key=AZURE_API_KEY,
    deployment_names=DEPLOYMENTS,
    api_version=API_VERSION
)

@app.post("/chat")
async def chat(request: Request):
    try:
        payload = await request.json()
        response = await load_balancer.forward_request(payload)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))