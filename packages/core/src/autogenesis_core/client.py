"""CodexClient — Direct integration with OpenAI Responses API.

Replaces ModelRouter + LiteLLM. Uses httpx for async HTTP
and httpx-sse for SSE stream parsing. Authenticates via
CredentialProvider (OAuth tokens injected by host gateway).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from httpx_sse import aconnect_sse
from pydantic import BaseModel, Field

from autogenesis_core.models import Message, TokenUsage, ToolCall, ToolDefinition
from autogenesis_core.responses import (
    AuthenticationError,
    RateLimitError,
    ResponseEvent,
    ResponseEventType,
    ServerError,
    messages_to_response_input,
    parse_sse_event,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from autogenesis_core.credentials import CredentialProvider

logger = structlog.get_logger()


class CodexClientConfig(BaseModel):
    """Configuration for the Codex API client."""

    model: str = "gpt-5.3-codex"
    api_base_url: str = "https://api.openai.com/v1"
    timeout: float = 300.0
    max_retries: int = 3


class CompletionResult(BaseModel):
    """Result from a Responses API call."""

    text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    response_id: str = ""


class CodexClient:
    """Async client for the OpenAI Responses API."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        config: CodexClientConfig | None = None,
    ) -> None:
        self._creds = credential_provider
        self._config = config or CodexClientConfig()
        self._http = httpx.AsyncClient(timeout=self._config.timeout)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def _build_headers(self) -> dict[str, str]:
        token = await self._creds.get_access_token()
        account_id = await self._creds.get_account_id()
        return {
            "Authorization": f"Bearer {token}",
            "ChatGPT-Account-ID": account_id,
            "Content-Type": "application/json",
        }

    def _build_request_body(
        self,
        messages: list[Message],
        instructions: str,
        tools: list[ToolDefinition] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._config.model,
            "instructions": instructions,
            "input": messages_to_response_input(messages),
            "stream": True,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]
        return body

    def _handle_http_error(
        self,
        status_code: int,
        body: dict[str, Any],
    ) -> None:
        """Raise typed exception based on HTTP status code."""
        error = body.get("error", {})
        message = error.get("message", f"HTTP {status_code}")

        if status_code == 401:  # noqa: PLR2004
            raise AuthenticationError(message)
        if status_code == 429:  # noqa: PLR2004
            raise RateLimitError(message)
        if status_code >= 500:  # noqa: PLR2004
            raise ServerError(message)

    async def create_response(
        self,
        messages: list[Message],
        instructions: str = "",
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[ResponseEvent]:
        """Stream a response from the Responses API.

        Yields ResponseEvent objects as they arrive via SSE.
        """
        headers = await self._build_headers()
        body = self._build_request_body(messages, instructions, tools)
        url = f"{self._config.api_base_url}/responses"

        async with aconnect_sse(
            self._http,
            "POST",
            url,
            json=body,
            headers=headers,
        ) as event_source:
            if event_source.response.status_code != 200:  # noqa: PLR2004
                error_body = json.loads(await event_source.response.aread())
                self._handle_http_error(
                    event_source.response.status_code,
                    error_body,
                )

            async for sse in event_source.aiter_sse():
                event = parse_sse_event(sse.event, sse.data)
                yield event

    async def create_response_sync(
        self,
        messages: list[Message],
        instructions: str = "",
        tools: list[ToolDefinition] | None = None,
    ) -> CompletionResult:
        """Non-streaming convenience method. Collects full response."""
        result = CompletionResult()
        text_parts: list[str] = []

        async for event in self.create_response(messages, instructions, tools):
            if event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA:
                text_parts.append(event.data.get("delta", ""))

            elif event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE:
                call_id = event.data.get("call_id", "")
                name = event.data.get("name", "")
                args_str = event.data.get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {"raw": args_str}
                result.tool_calls.append(
                    ToolCall(id=call_id, name=name, arguments=args),
                )

            elif event.event_type == ResponseEventType.COMPLETED:
                response_data = event.data.get("response", {})
                usage_data = response_data.get("usage", {})
                result.usage = TokenUsage(
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )
                result.response_id = response_data.get("id", "")

        result.text = "".join(text_parts)
        return result
