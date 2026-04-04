from __future__ import annotations

import pytest

from autogenesis_tui.app import AutogenesisApp
from autogenesis_tui.widgets import AgentStream, EmployeeRoster, InputBar, RightPanel, StatusBar


@pytest.mark.asyncio
async def test_app_composes_all_widgets():
    app = AutogenesisApp(auto_start=False)
    async with app.run_test() as pilot:
        assert pilot.app.query_one(StatusBar) is not None
        assert pilot.app.query_one(EmployeeRoster) is not None
        assert pilot.app.query_one(AgentStream) is not None
        assert pilot.app.query_one(RightPanel) is not None
        assert pilot.app.query_one(InputBar) is not None


@pytest.mark.asyncio
async def test_ws_event_agent_delta_updates_stream():
    app = AutogenesisApp(auto_start=False)
    async with app.run_test() as pilot:
        app.handle_ws_event({
            "method": "item/agentMessage/delta",
            "params": {"delta": "hello", "itemId": "i1", "threadId": "t1", "turnId": "turn1"},
        })
        await pilot.pause()
        stream = pilot.app.query_one(AgentStream)
        assert any(e.text == "hello" for e in stream.entries)


@pytest.mark.asyncio
async def test_ws_event_token_usage_updates_status_bar():
    app = AutogenesisApp(auto_start=False)
    async with app.run_test() as pilot:
        app.handle_ws_event({
            "method": "thread/tokenUsage/updated",
            "params": {
                "threadId": "t1",
                "turnId": "turn1",
                "tokenUsage": {
                    "total": {
                        "totalTokens": 5000,
                        "inputTokens": 3000,
                        "outputTokens": 2000,
                        "cachedInputTokens": 0,
                        "reasoningOutputTokens": 0,
                    },
                    "last": {
                        "totalTokens": 100,
                        "inputTokens": 60,
                        "outputTokens": 40,
                        "cachedInputTokens": 0,
                        "reasoningOutputTokens": 0,
                    },
                },
            },
        })
        await pilot.pause()
        bar = pilot.app.query_one(StatusBar)
        assert bar.session_tokens == 5000
