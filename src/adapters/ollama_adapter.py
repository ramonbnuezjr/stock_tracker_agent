"""Ollama adapter for local LLM inference."""

import logging
from typing import Any

import ollama

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Error communicating with Ollama."""

    pass


class OllamaAdapter:
    """Adapter for local LLM inference via Ollama.

    Args:
        model: The Ollama model name (e.g., 'mistral:7b').
        host: The Ollama API host URL.

    Returns:
        An OllamaAdapter instance.
    """

    def __init__(
        self,
        model: str = "mistral:7b",
        host: str = "http://localhost:11434",
    ) -> None:
        """Initialize the Ollama adapter.

        Args:
            model: The model name to use.
            host: The Ollama API host URL.
        """
        self.model = model
        self.host = host
        self._client: ollama.Client | None = None

    @property
    def client(self) -> ollama.Client:
        """Get or create the Ollama client.

        Returns:
            The Ollama client instance.
        """
        if self._client is None:
            self._client = ollama.Client(host=self.host)
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 256,
    ) -> str:
        """Generate text using the LLM.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0.0 - 1.0).
            max_tokens: Maximum tokens in the response.

        Returns:
            The generated text.

        Raises:
            OllamaError: If generation fails.
        """
        try:
            messages: list[dict[str, Any]] = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })

            messages.append({
                "role": "user",
                "content": prompt,
            })

            logger.debug("Generating with model %s", self.model)

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            content = response.get("message", {}).get("content", "")

            if not content:
                raise OllamaError("Empty response from Ollama")

            logger.debug("Generated %d characters", len(content))
            return content.strip()

        except ollama.ResponseError as e:
            logger.error("Ollama response error: %s", e)
            raise OllamaError(f"Ollama error: {e}")
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            raise OllamaError(f"Failed to generate: {e}")

    def is_available(self) -> bool:
        """Check if Ollama is available and the model is loaded.

        Returns:
            True if Ollama is ready to serve requests.
        """
        try:
            models = self.client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            # Check if our model (or base name) is available
            base_model = self.model.split(":")[0]
            return any(
                base_model in name for name in model_names
            )
        except Exception as e:
            logger.warning("Ollama not available: %s", e)
            return False

    def pull_model(self) -> bool:
        """Pull the model if not already available.

        Returns:
            True if model is ready, False if pull failed.
        """
        try:
            logger.info("Pulling model %s...", self.model)
            self.client.pull(self.model)
            return True
        except Exception as e:
            logger.error("Failed to pull model: %s", e)
            return False
