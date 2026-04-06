"""Tests for Twitter API signing gateway."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from threading import Thread

import pytest
from autogenesis_twitter.gateway import build_gateway_server


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

    def _request(
        self,
        server,
        path,
        method="GET",
        data=None,
        headers=None,
    ) -> urllib.request.Request:
        """Make a request to the test server."""
        port = server.server_address[1]
        url = f"http://127.0.0.1:{port}{path}"
        req = urllib.request.Request(url, method=method, headers=headers or {})  # noqa: S310
        if data:
            req.data = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
        return req

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
        # The request will fail because we can't reach Twitter API in tests,
        # but it should NOT be a 401 (that would mean our gateway rejected it).
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req)  # noqa: S310
        assert exc_info.value.code != 401
        thread.join(timeout=5)
