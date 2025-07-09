import httpx
from itertools import cycle
from typing import List

class AzureOpenAILoadBalancer:
    def __init__(self, base_url: str, api_key: str, deployment_names: List[str], api_version: str):
        self.base_url = base_url
        self.api_key = api_key
        self.api_version = api_version
        self.deployments = cycle(deployment_names)  # round-robin iterator

    async def forward_request(self, payload: dict):
        deployment_name = next(self.deployments)
        endpoint = f"{self.base_url}/openai/deployments/{deployment_name}/chat/completions?api-version={self.api_version}"

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()