"""llama.cpp adapter for in-process LLM inference (e.g. Phi-3 Mini)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None  # type: ignore[misc, assignment]


class LlamaCppError(Exception):
    """Error loading or calling the llama.cpp model."""

    pass


class LlamaCppAdapter:
    """Adapter for in-process LLM inference via llama-cpp-python.

    Loads a GGUF model from path (lazy on first generate). Suitable for
    Phi-3 Mini and other small models on 8GB RAM.

    Args:
        model_path: Path to the GGUF model file.
        n_ctx: Context window size (e.g. 2048).
        n_gpu_layers: Layers to offload to GPU (-1 for Metal on Mac).

    Returns:
        A LlamaCppAdapter instance.
    """

    def __init__(
        self,
        model_path: str | Path = "",
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
    ) -> None:
        """Initialize the adapter.

        Args:
            model_path: Path to the GGUF file.
            n_ctx: Context size.
            n_gpu_layers: GPU layers (-1 for all on Metal).
        """
        self.model_path = Path(model_path) if model_path else Path()
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llama: Any = None

    def _ensure_loaded(self) -> None:
        """Load the model on first use."""
        if self._llama is not None:
            return
        if Llama is None:
            raise LlamaCppError(
                "llama-cpp-python is not installed. "
                "Install with: pip install llama-cpp-python "
                "(on Mac M2: CMAKE_ARGS=\"-DGGML_METAL=on\" pip install llama-cpp-python)"
            )
        if not self.model_path or not self.model_path.exists():
            raise LlamaCppError(
                f"Model path does not exist or is empty: {self.model_path!s}"
            )
        logger.info("Loading LLM from %s (n_ctx=%s, n_gpu_layers=%s)",
                    self.model_path, self.n_ctx, self.n_gpu_layers)
        self._llama = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
            verbose=False,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
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
            LlamaCppError: If generation fails.
        """
        self._ensure_loaded()
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._llama.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.error("llama.cpp generation failed: %s", e)
            raise LlamaCppError(f"Failed to generate: {e}") from e

        choices = response.get("choices", [])
        if not choices:
            raise LlamaCppError("Empty response from llama.cpp")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise LlamaCppError("Empty content in response")
        logger.debug("Generated %d characters", len(content))
        return content.strip()

    def is_available(self) -> bool:
        """Check if the model file exists and llama-cpp-python is installed.

        Does not load the model; use generate() to load on first use.

        Returns:
            True if the model path exists and llama-cpp-python is installed.
        """
        if Llama is None:
            return False
        if self._llama is not None:
            return True
        return bool(self.model_path and self.model_path.exists())
