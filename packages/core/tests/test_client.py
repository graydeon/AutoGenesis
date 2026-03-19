"""Tests for CodexClient — Responses API integration."""

from __future__ import annotations

import pytest
from autogenesis_core.client import CodexClient, CodexClientConfig
from autogenesis_core.credentials import CredentialProvider
from autogenesis_core.models import Message, ToolDefinition
from autogenesis_core.responses import (
    AuthenticationError,
    RateLimitError,
    ServerError,
)


class MockCredentialProvider(CredentialProvider):
    async def get_access_token(self) -> str:
        return "test_token"

    async def get_account_id(self) -> str:
        return "test_account"


class TestCodexClientConfig:
    def test_defaults(self):
        cfg = CodexClientConfig()
        assert cfg.model == "gpt-5.3-codex"
        assert cfg.api_base_url == "https://api.openai.com/v1"

    def test_custom_model(self):
        cfg = CodexClientConfig(model="gpt-5.4")
        assert cfg.model == "gpt-5.4"


class TestCodexClientHeaders:
    async def test_builds_correct_headers(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        headers = await client._build_headers()
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["ChatGPT-Account-ID"] == "test_account"
        assert headers["Content-Type"] == "application/json"
        await client.close()


class TestCodexClientRequestBody:
    def test_builds_request(self):
        client = CodexClient(credential_provider=MockCredentialProvider())
        messages = [Message(role="user", content="hello")]
        tools = [ToolDefinition(name="bash", description="Run commands", parameters={})]

        body = client._build_request_body(
            messages=messages,
            instructions="You are a helpful agent.",
            tools=tools,
        )
        assert body["model"] == "gpt-5.3-codex"
        assert body["stream"] is True
        assert body["instructions"] == "You are a helpful agent."
        assert len(body["tools"]) == 1
        assert body["tools"][0]["type"] == "function"
        assert body["tools"][0]["name"] == "bash"


class TestCodexClientErrorHandling:
    async def test_401_raises_auth_error(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(AuthenticationError):
            client._handle_http_error(401, {"error": {"message": "Unauthorized"}})
        await client.close()

    async def test_429_raises_rate_limit(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(RateLimitError):
            client._handle_http_error(429, {"error": {"message": "Rate limited"}})
        await client.close()

    async def test_500_raises_server_error(self):
        provider = MockCredentialProvider()
        client = CodexClient(credential_provider=provider)
        with pytest.raises(ServerError):
            client._handle_http_error(500, {"error": {"message": "Internal"}})
        await client.close()
