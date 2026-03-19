"""Tests for credential providers."""

from __future__ import annotations

import json

import pytest
from autogenesis_core.credentials import (
    CredentialProvider,
    EnvCredentialProvider,
    FileCredentialProvider,
    GatewayCredentialProvider,
)


class TestCredentialProviderABC:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            CredentialProvider()


class TestEnvCredentialProvider:
    async def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("AUTOGENESIS_ACCESS_TOKEN", "tok_123")
        monkeypatch.setenv("AUTOGENESIS_ACCOUNT_ID", "acct_456")
        provider = EnvCredentialProvider()
        assert await provider.get_access_token() == "tok_123"
        assert await provider.get_account_id() == "acct_456"

    async def test_missing_token_raises(self, monkeypatch):
        monkeypatch.delenv("AUTOGENESIS_ACCESS_TOKEN", raising=False)
        provider = EnvCredentialProvider()
        with pytest.raises(RuntimeError, match="AUTOGENESIS_ACCESS_TOKEN"):
            await provider.get_access_token()

    async def test_missing_account_id_raises(self, monkeypatch):
        monkeypatch.delenv("AUTOGENESIS_ACCOUNT_ID", raising=False)
        provider = EnvCredentialProvider()
        with pytest.raises(RuntimeError, match="AUTOGENESIS_ACCOUNT_ID"):
            await provider.get_account_id()


class TestFileCredentialProvider:
    async def test_reads_auth_json(self, tmp_path):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(
            json.dumps(
                {
                    "access_token": "file_tok",
                    "account_id": "file_acct",
                    "refresh_token": "refresh_tok",
                }
            )
        )
        provider = FileCredentialProvider(auth_file)
        assert await provider.get_access_token() == "file_tok"
        assert await provider.get_account_id() == "file_acct"

    async def test_missing_file_raises(self, tmp_path):
        provider = FileCredentialProvider(tmp_path / "missing.json")
        with pytest.raises(FileNotFoundError):
            await provider.get_access_token()

    async def test_reads_fresh_on_each_call(self, tmp_path):
        auth_file = tmp_path / "auth.json"
        auth_file.write_text(json.dumps({"access_token": "v1", "account_id": "acct"}))
        provider = FileCredentialProvider(auth_file)
        assert await provider.get_access_token() == "v1"

        auth_file.write_text(json.dumps({"access_token": "v2", "account_id": "acct"}))
        assert await provider.get_access_token() == "v2"


class TestGatewayCredentialProvider:
    async def test_reads_from_well_known_path(self, tmp_path):
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps({"access_token": "gw_tok", "account_id": "gw_acct"}))
        provider = GatewayCredentialProvider(gateway_path=cred_file)
        assert await provider.get_access_token() == "gw_tok"
        assert await provider.get_account_id() == "gw_acct"

    async def test_missing_gateway_file_raises(self, tmp_path):
        provider = GatewayCredentialProvider(gateway_path=tmp_path / "nope.json")
        with pytest.raises(FileNotFoundError):
            await provider.get_access_token()
