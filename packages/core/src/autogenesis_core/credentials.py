"""Credential providers for accessing OAuth tokens.

The VM-side AutoGenesis never performs OAuth directly. It reads tokens
injected by the host-side gateway via one of these providers.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path


class CredentialProvider(ABC):
    """Abstract base for reading OAuth credentials."""

    @abstractmethod
    async def get_access_token(self) -> str: ...

    @abstractmethod
    async def get_account_id(self) -> str: ...


class EnvCredentialProvider(CredentialProvider):
    """Reads credentials from environment variables.

    Expects AUTOGENESIS_ACCESS_TOKEN and AUTOGENESIS_ACCOUNT_ID.
    """

    async def get_access_token(self) -> str:
        token = os.environ.get("AUTOGENESIS_ACCESS_TOKEN")
        if not token:
            msg = "AUTOGENESIS_ACCESS_TOKEN environment variable not set"
            raise RuntimeError(msg)
        return token

    async def get_account_id(self) -> str:
        account_id = os.environ.get("AUTOGENESIS_ACCOUNT_ID")
        if not account_id:
            msg = "AUTOGENESIS_ACCOUNT_ID environment variable not set"
            raise RuntimeError(msg)
        return account_id


class FileCredentialProvider(CredentialProvider):
    """Reads credentials from an auth.json file.

    For local dev / host-side usage without a VM.
    Reads fresh on every call so external refresh is picked up.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def _read(self) -> dict[str, str]:
        data: dict[str, str] = json.loads(self._path.read_text())
        return data

    async def get_access_token(self) -> str:
        return self._read()["access_token"]

    async def get_account_id(self) -> str:
        return self._read()["account_id"]


_DEFAULT_GATEWAY_PATH = Path("/run/autogenesis/credentials.json")


class GatewayCredentialProvider(CredentialProvider):
    """Reads credentials from a host-mounted file.

    The host-side gateway writes credentials to a well-known path
    and refreshes them atomically. This provider reads fresh on each call.

    Default path: /run/autogenesis/credentials.json
    """

    def __init__(self, gateway_path: Path = _DEFAULT_GATEWAY_PATH) -> None:
        self._path = gateway_path

    def _read(self) -> dict[str, str]:
        data: dict[str, str] = json.loads(self._path.read_text())
        return data

    async def get_access_token(self) -> str:
        return self._read()["access_token"]

    async def get_account_id(self) -> str:
        return self._read()["account_id"]
