"""Host-side OAuth PKCE authentication for OpenAI Codex.

This module runs on the HOST machine, not inside the VM.
It handles the browser-based OAuth flow, token exchange,
credential storage, and token refresh.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import stat
import webbrowser
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import jwt
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class OAuthCredentials(BaseModel):
    """Stored OAuth credentials."""

    access_token: str
    refresh_token: str
    id_token: str
    account_id: str
    plan_type: str
    last_refresh: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuthConfig(BaseModel):
    """OAuth configuration."""

    client_id: str = "app_EMoamEEZ73f0CkXaXp7hrann"
    auth_base_url: str = "https://auth.openai.com"
    callback_port: int = 1455
    scopes: list[str] = Field(
        default_factory=lambda: ["openid", "profile", "email", "offline_access"],
    )


def get_credentials_path() -> Path:
    """Get the path where OAuth credentials are stored."""
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(xdg) / "autogenesis" / "auth.json"


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE verifier and S256 challenge."""
    verifier = secrets.token_urlsafe(64)  # 86 chars, within 43-128 range
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def save_credentials(creds: OAuthCredentials, path: Path | None = None) -> None:
    """Save credentials to disk with restrictive permissions."""
    path = path or get_credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(creds.model_dump_json(indent=2))
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600


def load_credentials(path: Path | None = None) -> OAuthCredentials:
    """Load credentials from disk."""
    path = path or get_credentials_path()
    return OAuthCredentials.model_validate_json(path.read_text())


def is_token_expiring(creds: OAuthCredentials, buffer_seconds: int = 300) -> bool:
    """Check if the access token expires within buffer_seconds (default 5 min)."""
    try:
        claims = _extract_claims(creds.access_token)
        exp = claims.get("exp")
        if exp is None:
            return False
        expiry = datetime.fromtimestamp(exp, tz=UTC)
        return datetime.now(UTC) >= expiry - timedelta(seconds=buffer_seconds)
    except Exception:  # noqa: BLE001
        return False


def _extract_claims(id_token: str) -> dict[str, Any]:
    """Decode JWT id_token to extract claims (no signature verification)."""
    claims: dict[str, Any] = jwt.decode(
        id_token,
        options={"verify_signature": False, "verify_exp": False},
    )
    return claims


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback."""

    def do_GET(self) -> None:  # noqa: N802, RUF100
        qs = parse_qs(urlparse(self.path).query)
        server: _CallbackServer = self.server  # type: ignore[assignment]
        server.auth_code = qs.get("code", [None])[0]
        server.auth_state = qs.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Login successful. You can close this tab.</h1>")

    def log_message(self, *_args: object) -> None:
        pass  # suppress HTTP server logs


class _CallbackServer(HTTPServer):
    auth_code: str | None = None
    auth_state: str | None = None


def login(config: AuthConfig | None = None) -> OAuthCredentials:
    """Run the full PKCE OAuth login flow."""
    config = config or AuthConfig()
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)
    redirect_uri = f"http://localhost:{config.callback_port}"

    params = urlencode(
        {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes),
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
    )
    auth_url = f"{config.auth_base_url}/authorize?{params}"

    logger.info("opening_browser_for_login", url=auth_url)
    webbrowser.open(auth_url)

    server = _CallbackServer(("127.0.0.1", config.callback_port), _CallbackHandler)
    server.handle_request()

    if not server.auth_code:
        msg = "No authorization code received from callback"
        raise RuntimeError(msg)

    token_response = httpx.post(
        f"{config.auth_base_url}/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "code": server.auth_code,
            "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        },
    )
    token_response.raise_for_status()
    tokens = token_response.json()

    claims = _extract_claims(tokens["id_token"])
    auth_claims = claims.get("https://api.openai.com/auth", {})

    creds = OAuthCredentials(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        id_token=tokens["id_token"],
        account_id=auth_claims.get("chatgpt_account_id", ""),
        plan_type=auth_claims.get("chatgpt_plan_type", "unknown"),
    )

    save_credentials(creds)
    logger.info("login_successful", plan_type=creds.plan_type)
    return creds


def refresh_token(config: AuthConfig | None = None, path: Path | None = None) -> OAuthCredentials:
    """Refresh the access token using the stored refresh token."""
    config = config or AuthConfig()
    creds = load_credentials(path)

    response = httpx.post(
        f"{config.auth_base_url}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": config.client_id,
            "refresh_token": creds.refresh_token,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    claims = _extract_claims(tokens.get("id_token", creds.id_token))
    auth_claims = claims.get("https://api.openai.com/auth", {})

    updated = OAuthCredentials(
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token", creds.refresh_token),
        id_token=tokens.get("id_token", creds.id_token),
        account_id=auth_claims.get("chatgpt_account_id", creds.account_id),
        plan_type=auth_claims.get("chatgpt_plan_type", creds.plan_type),
    )

    save_credentials(updated, path)
    logger.info("token_refreshed")
    return updated
