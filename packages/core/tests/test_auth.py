"""Tests for host-side OAuth authentication."""

from __future__ import annotations

import base64
import hashlib

import pytest
from autogenesis_core.auth import (
    AuthConfig,
    OAuthCredentials,
    generate_pkce_pair,
    get_credentials_path,
    load_credentials,
    save_credentials,
)


class TestPKCE:
    def test_verifier_length(self):
        verifier, _challenge = generate_pkce_pair()
        assert 43 <= len(verifier) <= 128

    def test_challenge_is_sha256_of_verifier(self):
        verifier, challenge = generate_pkce_pair()
        expected = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        assert challenge == expected

    def test_no_padding_in_challenge(self):
        _, challenge = generate_pkce_pair()
        assert "=" not in challenge

    def test_unique_each_call(self):
        v1, _ = generate_pkce_pair()
        v2, _ = generate_pkce_pair()
        assert v1 != v2


class TestCredentialStorage:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "auth.json"
        creds = OAuthCredentials(
            access_token="at_123",  # noqa: S106
            refresh_token="rt_456",  # noqa: S106
            id_token="idt_789",  # noqa: S106
            account_id="acct_abc",
            plan_type="plus",
        )
        save_credentials(creds, path)
        loaded = load_credentials(path)
        assert loaded.access_token == "at_123"  # noqa: S105
        assert loaded.account_id == "acct_abc"

    def test_file_permissions(self, tmp_path):
        path = tmp_path / "auth.json"
        creds = OAuthCredentials(
            access_token="a",  # noqa: S106
            refresh_token="r",  # noqa: S106
            id_token="i",  # noqa: S106
            account_id="acct",
            plan_type="plus",
        )
        save_credentials(creds, path)
        mode = oct(path.stat().st_mode)[-3:]
        assert mode == "600"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_credentials(tmp_path / "nope.json")


class TestAuthConfig:
    def test_defaults(self):
        cfg = AuthConfig()
        assert cfg.client_id == "app_EMoamEEZ73f0CkXaXp7hrann"
        assert cfg.auth_base_url == "https://auth.openai.com"


class TestGetCredentialsPath:
    def test_returns_path(self):
        path = get_credentials_path()
        assert str(path).endswith("autogenesis/auth.json")
