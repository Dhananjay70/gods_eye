"""
LLM Router — multi-model routing with fallback chain.

Providers:
  1. Anthropic (Claude) — cloud, highest quality
  2. Ollama — local, privacy-preserving
  3. Template — no LLM, rule-based fallback
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from openclaw.config import ANTHROPIC_API_KEY, LLM_PROVIDER, OLLAMA_BASE_URL

log = logging.getLogger("openclaw.llm")


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    text: str = ""
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    success: bool = True
    error: str = ""


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def generate(self, system: str, prompt: str) -> LLMResponse:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...


class AnthropicProvider(LLMProvider):
    """Claude API provider."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or ANTHROPIC_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, system: str, prompt: str) -> LLMResponse:
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text if response.content else ""
            return LLMResponse(
                text=text,
                model="claude-sonnet-4-5-20250929",
                provider="anthropic",
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            )
        except Exception as e:
            log.warning("Anthropic call failed: %s", e)
            return LLMResponse(success=False, error=str(e), provider="anthropic")


class OllamaProvider(LLMProvider):
    """Local Ollama provider."""

    def __init__(self, base_url: str = "", model: str = "llama3.1"):
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model

    def is_available(self) -> bool:
        try:
            import httpx

            resp = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    async def generate(self, system: str, prompt: str) -> LLMResponse:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "system": system,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                data = resp.json()
                return LLMResponse(
                    text=data.get("response", ""),
                    model=self.model,
                    provider="ollama",
                )
        except Exception as e:
            log.warning("Ollama call failed: %s", e)
            return LLMResponse(success=False, error=str(e), provider="ollama")


class TemplateProvider(LLMProvider):
    """Fallback: rule-based template generation (no LLM)."""

    def is_available(self) -> bool:
        return True

    async def generate(self, system: str, prompt: str) -> LLMResponse:
        # Extract key data from the prompt to fill a basic template
        text = (
            "## Disclosure Draft (Template-Generated)\n\n"
            "**Note:** This draft was generated using a rule-based template "
            "because no LLM provider was available. Human review is required.\n\n"
            "### 1. Nature and Scope\n"
            "[CONFIDENCE: LOW]\n"
            "A cybersecurity incident was detected through automated scanning. "
            "Further investigation is required to determine full scope.\n\n"
            "### 2. Impact on Data and Systems\n"
            "[CONFIDENCE: LOW]\n"
            "The automated assessment identified potential security concerns. "
            "A manual review is needed to determine data impact.\n\n"
            "### 3. Material Impact Assessment\n"
            "[CONFIDENCE: LOW]\n"
            "Preliminary automated scoring indicates this incident requires "
            "further materiality assessment by qualified personnel.\n\n"
            "### 4. Remediation Status\n"
            "[CONFIDENCE: LOW]\n"
            "Remediation efforts are pending the completion of the investigation. "
            "Immediate containment measures should be evaluated.\n"
        )
        return LLMResponse(text=text, model="template", provider="template")


class LLMRouter:
    """Routes LLM requests through a fallback chain of providers."""

    def __init__(self):
        self.providers: list[LLMProvider] = []
        self._init_providers()

    def _init_providers(self) -> None:
        """Set up the provider chain based on configuration."""
        # Always try in this order: configured provider first, then fallbacks
        if LLM_PROVIDER == "anthropic":
            self.providers = [AnthropicProvider(), OllamaProvider(), TemplateProvider()]
        elif LLM_PROVIDER == "ollama":
            self.providers = [OllamaProvider(), AnthropicProvider(), TemplateProvider()]
        else:
            self.providers = [AnthropicProvider(), OllamaProvider(), TemplateProvider()]

    async def route(self, system: str, prompt: str) -> LLMResponse:
        """Try each provider in order until one succeeds."""
        for provider in self.providers:
            if not provider.is_available():
                continue
            response = await provider.generate(system, prompt)
            if response.success:
                return response
            log.warning("Provider %s failed, trying next...", type(provider).__name__)

        # Should never reach here because TemplateProvider always works
        return await TemplateProvider().generate(system, prompt)
