"""
Model adapter layer.

Supports multiple inference backends via a common interface:
  - "mock"         – deterministic fallback for testing / model-unavailable states
  - "huggingface"  – local Transformers pipeline
  - "hf_api"       – Hugging Face Inference API (serverless)
  - "gemini"       – Google Gemini API (requires google-generativeai package)

Switch backend by setting MODEL_PROVIDER in .env.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_ADAPTER: Optional["BaseModelAdapter"] = None


class BaseModelAdapter(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_new_tokens: int = 256) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...


# ---------------------------------------------------------------------------
# Mock adapter (always available, used when model not configured/downloaded)
# ---------------------------------------------------------------------------
class MockAdapter(BaseModelAdapter):
    """
    Safe fallback that makes the unavailability visible to the user.
    Does NOT hallucinate answers – only surfaces the retrieved context.
    """
    @property
    def is_available(self) -> bool:
        return True

    @property
    def model_id(self) -> str:
        return "mock-fallback"

    def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
        return (
            "⚠️ **Language model is not available.**\n\n"
            "The configured model could not be loaded. "
            "Please check your MODEL_PROVIDER and MODEL_ID settings and ensure "
            "the model is downloaded or the API credentials are configured.\n\n"
            "The retrieved document context is shown in the Sources section."
        )


# ---------------------------------------------------------------------------
# Hugging Face local pipeline adapter
# ---------------------------------------------------------------------------
class HuggingFaceAdapter(BaseModelAdapter):
    def __init__(self):
        self._pipeline = None
        self._available = False
        self._error: Optional[str] = None
        self._init()

    def _init(self):
        try:
            import torch
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

            model_path = settings.MODEL_PATH or settings.MODEL_ID
            logger.info("Loading HuggingFace model '%s' (this may take a while)…", model_path)

            kwargs = {
                "model": model_path,
                "trust_remote_code": False,
                "device_map": "auto",
            }
            if settings.HF_API_TOKEN:
                kwargs["token"] = settings.HF_API_TOKEN

            self._pipeline = pipeline(
                "text-generation",
                **kwargs,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            )
            self._available = True
            logger.info("HuggingFace model loaded: %s", model_path)
        except Exception as exc:
            self._error = str(exc)
            logger.warning("HuggingFace model unavailable: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def model_id(self) -> str:
        return settings.MODEL_ID

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        if not self._available:
            return MockAdapter().generate(prompt, max_new_tokens)
        try:
            out = self._pipeline(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=settings.TEMPERATURE,
                do_sample=settings.TEMPERATURE > 0,
                pad_token_id=self._pipeline.tokenizer.eos_token_id,
                return_full_text=False,
            )
            return out[0]["generated_text"].strip()
        except Exception as exc:
            logger.error("Generation error: %s", exc)
            return f"Generation error: {exc}"


# ---------------------------------------------------------------------------
# Hugging Face Inference API adapter
# ---------------------------------------------------------------------------
class HFApiAdapter(BaseModelAdapter):
    def __init__(self):
        self._available = bool(settings.HF_API_TOKEN)
        if not self._available:
            logger.warning("HF_API_TOKEN not set – HF Inference API unavailable.")

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def model_id(self) -> str:
        return settings.MODEL_ID

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        if not self._available:
            return MockAdapter().generate(prompt, max_new_tokens)
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(model=settings.MODEL_ID, token=settings.HF_API_TOKEN)
            response = client.text_generation(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=settings.TEMPERATURE,
                return_full_text=False,
            )
            return response.strip()
        except Exception as exc:
            logger.error("HF API generation error: %s", exc)
            return f"HF API error: {exc}"


# ---------------------------------------------------------------------------
# Google Gemini API adapter
# ---------------------------------------------------------------------------
class GeminiAdapter(BaseModelAdapter):
    def __init__(self):
        self._available = False
        self._model = None
        try:
            import google.generativeai as genai
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set.")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(settings.MODEL_ID or "gemini-2.0-flash")
            self._available = True
            logger.info("Gemini adapter ready: %s", settings.MODEL_ID)
        except Exception as exc:
            logger.warning("Gemini adapter unavailable: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def model_id(self) -> str:
        return settings.MODEL_ID or "gemini"

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        if not self._available:
            return MockAdapter().generate(prompt, max_new_tokens)
        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini generation error: %s", exc)
            return f"Gemini API error: {exc}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_adapter() -> BaseModelAdapter:
    global _ADAPTER
    if _ADAPTER is not None:
        return _ADAPTER

    provider = settings.MODEL_PROVIDER.lower()
    if provider == "huggingface":
        _ADAPTER = HuggingFaceAdapter()
    elif provider == "hf_api":
        _ADAPTER = HFApiAdapter()
    elif provider == "gemini":
        _ADAPTER = GeminiAdapter()
    else:
        logger.warning("Unknown MODEL_PROVIDER '%s'. Using mock adapter.", provider)
        _ADAPTER = MockAdapter()

    if not _ADAPTER.is_available:
        logger.warning("Selected adapter '%s' is not available – falling back to mock.", provider)

    return _ADAPTER
