"""Tests for Twitter API signing gateway."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from threading import Thread
from unittest.mock import patch

import pytest
from autogenesis_twitter.gateway import build_gateway_server


class _FakeTwitterResponse:
    def read(self) -> bytes:
        return json.dumps({"data": {"id": "tweet-123"}}).encode()


class TestGatewayServer:
    @pytest.fixture
    def server(self):
        srv = build_gateway_server(
            host="127.0.0.1",
            port=0,  # OS-assigned port
            bearer_token="test_bearer",  # noqa: S106
            gateway_token="test-gw-token",  # noqa: S106
        )
        yield srv
        srv.server_close()

    def _request(  # noqa: PLR0913
        self,
        server,
        path,
        method="GET",
        data=None,
        headers=None,
        raw_data=None,
    ) -> urllib.request.Request:
        """Make a request to the test server."""
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}{path}"
        req = urllib.request.Request(url, method=method, headers=headers or {})  # noqa: S310
        if data:
            req.data = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        if raw_data is not None:
            req.data = raw_data
            req.add_header("Content-Type", "application/json")
        return req

    def test_gateway_token_required_by_default(self) -> None:
        with pytest.raises(ValueError, match="gateway_token"):
            build_gateway_server(host="127.0.0.1", port=0, bearer_token="test_bearer")  # noqa: S106

    def test_health_endpoint(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(server, "/health")
        resp = urllib.request.urlopen(req)  # noqa: S310
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["status"] == "ok"
        thread.join(timeout=5)

    def test_unknown_path_returns_404(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(server, "/unknown")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 404
        thread.join(timeout=5)

    def test_status_requires_auth(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(server, "/twitter/status")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 401
        thread.join(timeout=5)

    def test_status_with_auth_returns_configuration(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/status",
            headers={"Authorization": "Bearer test-gw-token"},
        )
        resp = urllib.request.urlopen(req)  # noqa: S310
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["authenticated"] is True
        thread.join(timeout=5)

    def test_tweet_without_auth_returns_401(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/tweet",
            method="POST",
            data={"text": "hello"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 401
        thread.join(timeout=5)

    def test_tweet_without_text_returns_400(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/tweet",
            method="POST",
            data={},
            headers={"Authorization": "Bearer test-gw-token"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 400
        thread.join(timeout=5)

    def test_tweet_with_invalid_json_returns_400(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/tweet",
            method="POST",
            raw_data=b"{",
            headers={"Authorization": "Bearer test-gw-token"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 400
        thread.join(timeout=5)

    def test_tweet_too_large_returns_400(self, server) -> None:
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/tweet",
            method="POST",
            data={"text": "x" * 281},
            headers={"Authorization": "Bearer test-gw-token"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code == 400
        thread.join(timeout=5)

    def test_tweet_with_auth_reaches_twitter_api(self, server) -> None:
        """With valid auth, gateway forwards to Twitter (not rejected as 401)."""
        thread = Thread(target=server.handle_request)
        thread.start()
        req = self._request(
            server,
            "/twitter/tweet",
            method="POST",
            data={"text": "test tweet"},
            headers={"Authorization": "Bearer test-gw-token"},
        )
        with patch("autogenesis_twitter.gateway.urlopen", return_value=_FakeTwitterResponse()):
            resp = urllib.request.urlopen(req)  # noqa: S310
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data["id"] == "tweet-123"
        assert data["tweet_id"] == "tweet-123"
        thread.join(timeout=5)
