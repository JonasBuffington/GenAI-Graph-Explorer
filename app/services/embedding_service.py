import asyncio
import os
import requests
from typing import Literal
from app.core.rag_config import VECTOR_DIMENSIONS

if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

class EmbeddingService:
    _API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent"

    def __init__(
        self,
        api_key: str,
        model_name: Literal["gemini-embedding-001", "text-embedding-004"] = "gemini-embedding-001"
    ):
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided.")
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = self._API_URL_TEMPLATE.format(model_name=self.model_name)

    def _make_request(self, text: str) -> requests.Response:
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        data = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": VECTOR_DIMENSIONS
        }
        return requests.post(self.api_url, headers=headers, json=data)

    async def get_embedding(self, text: str) -> list[float]:
        try:
            response = await asyncio.to_thread(self._make_request, text)
            response.raise_for_status()
            
            response_json = response.json()
            embedding = response_json.get("embedding", {}).get("values", [])
            
            if not embedding:
                raise ValueError("Failed to retrieve embedding from API response.")
                
            return embedding
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed: {e}")
            raise
        except (KeyError, ValueError) as e:
            print(f"Failed to parse API response: {e}")
            print(f"Raw response text: {response.text if 'response' in locals() else 'No response'}")
            raise

# Standalone test block
async def main():
    """
    A simple test function to verify the EmbeddingService works correctly.
    Requires a .env file with GEMINI_API_KEY in the project root.
    """
    print("Running EmbeddingService standalone test...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\nError: GEMINI_API_KEY not found in .env file.")
        return

    try:
        service = EmbeddingService(api_key=api_key)
        test_text = "This is a test to verify the embedding API call."
        print(f"Requesting embedding for: '{test_text}'")
        
        embedding_vector = await service.get_embedding(test_text)
        
        print(f"\nSuccessfully received embedding vector.")
        print(f"Vector dimensions: {len(embedding_vector)}")
        print(f"First 5 values: {embedding_vector[:5]}")
        print("\nTest PASSED. The direct API call was successful.")

    except Exception as e:
        print(f"\nTest FAILED: An error occurred: {e}")

if __name__ == "__main__":
    # Add dotenv for the standalone script if you don't have it
    # poetry add python-dotenv
    asyncio.run(main())