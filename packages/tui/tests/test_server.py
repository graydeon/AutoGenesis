from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from autogenesis_tui.server import AppServerManager


def test_find_free_port_returns_int():
    port = AppServerManager._find_free_port()
    assert isinstance(port, int)
    assert 1024 < port < 65536


@pytest.mark.asyncio
async def test_start_spawns_process():
    mgr = AppServerManager()
    mock_proc = MagicMock()
    mock_proc.returncode = None

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc
        port = await mgr.start()

    assert port > 0
    assert mgr.port == port
    assert mgr.is_running
    mock_exec.assert_called_once()
    cmd = mock_exec.call_args[0]
    assert cmd[0] == "codex"
    assert "app-server" in cmd
    assert any(f"ws://127.0.0.1:{port}" in str(a) for a in cmd)


@pytest.mark.asyncio
async def test_stop_terminates_process():
    mgr = AppServerManager()
    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.wait = AsyncMock()

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc
        await mgr.start()

    await mgr.stop()
    mock_proc.terminate.assert_called_once()
    assert not mgr.is_running


@pytest.mark.asyncio
async def test_stop_when_not_started_is_safe():
    mgr = AppServerManager()
    await mgr.stop()  # should not raise
