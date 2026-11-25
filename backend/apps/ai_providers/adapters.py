"""Provider-specific adapters behind one common interface."""
import json
import time

import requests


class AdapterError(Exception):
    """Bad input/credentials/safety - must not be retried on other providers."""


class TransientError(Exception):
    """Timeout, rate limit, 5xx - may fail over to the next provider."""


class BaseAdapter:
    transient_statuses = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, provider):
        self.provider = provider
        self.base_url = provider.base_url or self.default_base_url()
        self.model = provider.model or self.default_model()
        self.api_key = provider.api_key_decrypted

    def default_base_url(self):
        raise NotImplementedError

    def default_model(self):
        raise NotImplementedError

    def generate(self, prompt, system=None, max_tokens=512, temperature=0.7):
        raise NotImplementedError

    def _post(self, url, payload, headers):
        start = time.monotonic()
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.provider.timeout_seconds
            )
        except requests.Timeout as exc:
            raise TransientError("timeout") from exc
        except requests.RequestException as exc:
            raise TransientError(f"connection: {exc}") from exc
        latency_ms = int((time.monotonic() - start) * 1000)
        if response.status_code in self.transient_statuses:
            raise TransientError(f"http {response.status_code}: {response.text[:200]}")
        if response.status_code in (401, 403):
            raise AdapterError("invalid credentials")
        if response.status_code == 400:
            raise AdapterError(f"bad request: {response.text[:200]}")
        if response.status_code >= 400:
            raise AdapterError(f"http {response.status_code}: {response.text[:200]}")
        return response, latency_ms


class OpenAICompatibleAdapter(BaseAdapter):
    def default_base_url(self):
        return "https://api.openai.com/v1"

    def default_model(self):
        return "gpt-4o-mini"

    def generate(self, prompt, system=None, max_tokens=512, temperature=0.7):
        url = self.base_url.rstrip("/") + "/chat/completions"
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response, latency = self._post(
            url,
            {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
            {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        data = response.json()
        return {
            "text": (data.get("choices") or [{}])[0].get("message", {}).get("text", "") if data.get("choices") else "",
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
            "latency_ms": latency,
        }


class AnthropicAdapter(BaseAdapter):
    def default_base_url(self):
        return "https://api.anthropic.com/v1"

    def default_model(self):
        return "claude-3-5-haiku-latest"

    def generate(self, prompt, system=None, max_tokens=512, temperature=0.7):
        url = self.base_url.rstrip("/") + "/messages"
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        response, latency = self._post(
            url,
            payload,
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        )
        data = response.json()
        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
        usage = data.get("usage", {})
        return {
            "text": text,
            "tokens_in": usage.get("input_tokens", 0),
            "tokens_out": usage.get("output_tokens", 0),
            "latency_ms": latency,
        }


class GeminiAdapter(BaseAdapter):
    def default_base_url(self):
        return "https://generativelanguage.googleapis.com/v1beta"

    def default_model(self):
        return "gemini-1.5-flash"

    def generate(self, prompt, system=None, max_tokens=512, temperature=0.7):
        url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent"
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        if system:
            contents.insert(0, {"role": "user", "parts": [{"text": system}]})
        response, latency = self._post(
            url,
            {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
            },
            {"Content-Type": "application/json", "x-goog-api-key": self.api_key},
        )
        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][-1]["text"]
        except (KeyError, IndexError) as exc:
            raise TransientError(f"unexpected gemini response: {json.dumps(data)[:200]}") from exc
        usage = data.get("usageMetadata", {})
        return {
            "text": text,
            "tokens_in": usage.get("promptTokenCount", 0),
            "tokens_out": usage.get("candidatesTokenCount", 0),
            "latency_ms": latency,
        }


ADAPTERS = {
    "openai": OpenAICompatibleAdapter,
    "gemini": GeminiAdapter,
    "anthropic": AnthropicAdapter,
}


def get_adapter(provider):
    adapter_class = ADAPTERS.get(provider.adapter)
    if adapter_class is None:
        raise AdapterError(f"unknown adapter '{provider.adapter}'")
    return adapter_class(provider)
