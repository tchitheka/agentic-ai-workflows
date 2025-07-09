import httpx
from itertools import cycle
from typing import List
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class AzureOpenAILoadBalancer:
    def __init__(self, base_url: str, api_key: str, deployment_names: List[str], api_version: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_version = api_version
        self.deployments = cycle(deployment_names)

    async def forward_request(self, payload: dict):
        deployment_name = next(self.deployments)
        endpoint = f"{self.base_url}/openai/deployments/{deployment_name}/chat/completions?api-version={self.api_version}"

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        logger.info(f"Forwarding request to deployment: {deployment_name}")
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except httpx.TimeoutException:
                logger.error(f"Timeout error for deployment: {deployment_name}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise