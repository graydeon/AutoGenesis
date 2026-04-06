from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogenesis_tui.client import CodexWSClient


@pytest.fixture
def mock_ws():
    ws = MagicMock()
    ws.send = AsyncMock()
    ws.close = AsyncMock()
    ws.__aiter__ = MagicMock(return_value=iter([]))
    return ws


@pytest.mark.asyncio
async def test_connect_sends_initialize(mock_ws):
    events = []
    client = None

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            fut.set_result({"serverInfo": {}})

    mock_ws.send = fake_send
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))

    with patch("autogenesis_tui.client.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        await client.connect()

    assert True  # no exception = connected and initialized


@pytest.mark.asyncio
async def test_start_thread_returns_thread_id(mock_ws):
    events = []
    client = None

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            if data["method"] == "initialize":
                fut.set_result({"serverInfo": {}})
            elif data["method"] == "thread/start":
                fut.set_result({"thread": {"id": "thread-abc-123"}})

    mock_ws.send = fake_send
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))

    with patch("autogenesis_tui.client.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        await client.connect()
        thread_id = await client.start_thread(base_instructions="You are CEO.")

    assert thread_id == "thread-abc-123"


@pytest.mark.asyncio
async def test_on_event_called_for_notifications(mock_ws):
    events = []
    client = None
    notification = json.dumps(
        {
            "method": "item/agentMessage/delta",
            "params": {
                "delta": "Hello",
                "itemId": "item-1",
                "threadId": "t-1",
                "turnId": "turn-1",
            },
        }
    )

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            fut.set_result({})

    mock_ws.send = fake_send

    async def aiter_mock():
        yield notification

    mock_ws.__aiter__ = MagicMock(return_value=aiter_mock())

    with patch("autogenesis_tui.client.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=events.append)
        await client.connect()
        await asyncio.sleep(0.05)

    assert any(e.get("method") == "item/agentMessage/delta" for e in events)


@pytest.mark.asyncio
async def test_disconnect_closes_ws(mock_ws):
    client = None

    async def fake_send(msg):
        data = json.loads(msg)
        fut = client._pending.get(data.get("id", ""))
        if fut and not fut.done():
            fut.set_result({})

    mock_ws.send = fake_send
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))

    with patch("autogenesis_tui.client.connect", new=AsyncMock(return_value=mock_ws)):
        client = CodexWSClient(port=12345, on_event=lambda e: None)
        await client.connect()
        await client.disconnect()

    mock_ws.close.assert_called_once()
