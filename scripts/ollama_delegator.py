import logging
from typing import Optional

from opendiscourse import OllamaClient, ResultHandler


class OllamaDelegationError(Exception):
    """Base exception for delegation errors"""
    pass

class OllamaDelegator:
    def __init__(self, base_url: str = None):
        from config.api_config import OLLAMA_CONFIG
        config = OLLAMA_CONFIG
        self.client = OllamaClient(base_url or config["base_url"])
        self.logger = logging.getLogger(__name__)
        self.result_handler = ResultHandler()

    def delegate(
        self,
        prompt: str,
        model: str = "llama2",
        max_retries: int = 3,
        timeout: int = 300
    ) -> Optional[str]:
        """
        Delegate a prompt to Ollama with retry logic

        Args:
            prompt: Input prompt for the model
            model: Ollama model name
            max_retries: Number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            Model response or None on failure
        """
        for attempt in range(max_retries):
            try:
                response = self.client.generate(
                    prompt=prompt,
                    model=model,
                    timeout=timeout
                )
                return self.result_handler.process(response)

            except Exception as e:
                self.logger.error(
                    f"Attempt {attempt + 1} failed: {str(e)}",
                    exc_info=True
                )
                if attempt == max_retries - 1:
                    raise OllamaDelegationError(
                        f"Failed after {max_retries} attempts: {str(e)}"
                    ) from e

    def validate_model(self, model: str) -> bool:
        """Check if model is available locally"""
        try:
            return model in self.client.list_models()
        except Exception as e:
            self.logger.error(f"Model validation failed: {str(e)}")
            return False
