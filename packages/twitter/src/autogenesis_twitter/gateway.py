"""Twitter API signing gateway — HTTP server for host-side credential management.

Receives unsigned tweet requests, signs with real Twitter API v2 credentials,
and forwards to api.twitter.com. Credentials are never exposed to the VM/agent.

Configure host/port via CLI flags (defaults: 127.0.0.1:1456).
Twitter API credentials are read from environment variables (TWITTER_API_KEY, etc.).
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"
_MAX_REQUEST_BYTES = 8_192
_MAX_TWEET_CHARS = 280


class GatewayHandler(BaseHTTPRequestHandler):
    """HTTP handler for the Twitter signing gateway."""

    gateway_token: str = ""
    bearer_token: str = ""
    allow_unauthenticated: bool = False

    def _check_auth(self) -> bool:
        if not self.gateway_token:
            return self.allow_unauthenticated
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {self.gateway_token}"

    def _send_json(self, code: int, data: dict[str, Any]) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/twitter/status":
            if not self._check_auth():
                self._send_json(401, {"error": "unauthorized"})
                return
            self._send_json(
                200,
                {
                    "status": "ok",
                    "authenticated": bool(self.bearer_token),
                    "twitter_api_configured": bool(self.bearer_token),
                },
            )
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/twitter/tweet":
            self._handle_tweet()
        else:
            self._send_json(404, {"error": "not found"})

    def _read_json_body(self) -> dict[str, Any] | None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            self._send_json(400, {"error": "invalid content length"})
            return None
        if content_length > _MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "request body too large"})
            return None
        if content_length == 0:
            return {}

        raw_body = self.rfile.read(content_length)
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid json"})
            return None
        if not isinstance(body, dict):
            self._send_json(400, {"error": "json body must be an object"})
            return None
        return body

    def _handle_tweet(self) -> None:
        if not self._check_auth():
            self._send_json(401, {"error": "unauthorized"})
            return

        body = self._read_json_body()
        if body is None:
            return

        text = body.get("text", "")
        reply_to = body.get("reply_to_id")
        if not isinstance(text, str) or not text.strip():
            self._send_json(400, {"error": "text is required"})
            return
        if len(text) > _MAX_TWEET_CHARS:
            self._send_json(400, {"error": "text exceeds 280 characters"})
            return

        payload: dict[str, Any] = {"text": text}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}

        try:
            req = Request(  # noqa: S310
                f"{TWITTER_API_BASE}/tweets",
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            resp = urlopen(req, timeout=30)  # noqa: S310
            result = json.loads(resp.read())
            tweet_id = result.get("data", {}).get("id", "")
            self._send_json(200, {"success": True, "id": tweet_id, "tweet_id": tweet_id})
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.exception("twitter_api_error: status=%s body=%s", e.code, error_body)
            self._send_json(e.code, {"success": False, "error": error_body})
        except (URLError, TimeoutError) as e:
            logger.exception("twitter_api_connection_error")
            self._send_json(502, {"success": False, "error": str(e)})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        logger.debug(format, *args)


def build_gateway_server(  # noqa: PLR0913
    host: str = "127.0.0.1",
    port: int = 1456,
    api_key: str = "",
    api_secret: str = "",
    access_token: str = "",
    access_secret: str = "",
    bearer_token: str = "",
    gateway_token: str = "",
    *,
    allow_unauthenticated: bool = False,
) -> HTTPServer:
    """Build and return a gateway HTTP server (not started)."""
    if not gateway_token and not allow_unauthenticated:
        msg = "gateway_token is required unless allow_unauthenticated is enabled"
        raise ValueError(msg)
    server = HTTPServer((host, port), GatewayHandler)
    GatewayHandler.gateway_token = gateway_token
    GatewayHandler.bearer_token = bearer_token
    GatewayHandler.allow_unauthenticated = allow_unauthenticated
    # Store OAuth1 creds on server for future OAuth1.0a signing
    server.api_key = api_key  # type: ignore[attr-defined]
    server.api_secret = api_secret  # type: ignore[attr-defined]
    server.access_token = access_token  # type: ignore[attr-defined]
    server.access_secret = access_secret  # type: ignore[attr-defined]
    return server


if __name__ == "__main__":
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description="Twitter API Gateway")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1456)
    parser.add_argument("--gateway-token", default="")
    parser.add_argument("--allow-unauthenticated", action="store_true")
    args = parser.parse_args()

    srv = build_gateway_server(
        host=args.host,
        port=args.port,
        api_key=os.environ.get("TWITTER_API_KEY", ""),
        api_secret=os.environ.get("TWITTER_API_SECRET", ""),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN", ""),
        access_secret=os.environ.get("TWITTER_ACCESS_SECRET", ""),
        bearer_token=os.environ.get("TWITTER_BEARER_TOKEN", ""),
        gateway_token=args.gateway_token or os.environ.get("AUTOGENESIS_TWITTER_GATEWAY_TOKEN", ""),
        allow_unauthenticated=args.allow_unauthenticated,
    )
    sys.stdout.write(f"Twitter Gateway listening on {args.host}:{args.port}\n")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()
        sys.stdout.write("\nGateway stopped.\n")
