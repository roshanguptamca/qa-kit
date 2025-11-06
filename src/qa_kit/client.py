import os
import time
import json
import logging
import httpx
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TOKEN_CACHE = Path(".qa_token_cache.json")


class OAuth2Client:
    """
    Fetch and cache OAuth2 access token.
    Supports client_credentials flow.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        scope: Optional[str] = None,
    ):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.grant_type = grant_type
        self.scope = scope
        self.token_info = self._load_token_cache()

    def _load_token_cache(self) -> Dict:
        if TOKEN_CACHE.exists():
            try:
                return json.loads(TOKEN_CACHE.read_text())
            except Exception:
                logger.warning("⚠️ Token cache is corrupt. Ignoring.")
        return {}

    def _save_token_cache(self, token_info: Dict):
        try:
            TOKEN_CACHE.write_text(json.dumps(token_info))
        except Exception as e:
            logger.warning(f"⚠️ Could not save token cache: {e}")

    def _is_token_valid(self) -> bool:
        if not self.token_info:
            return False
        expires_at = self.token_info.get("expires_at", 0)
        return time.time() < expires_at - 30  # 30s buffer

    def get_token(self) -> str:
        """Return valid access token, fetch if expired."""
        if self._is_token_valid():
            return self.token_info["access_token"]

        logger.info("🔑 Fetching new OAuth2 token...")
        payload = {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            payload["scope"] = self.scope

        response = httpx.post(self.token_url, data=payload)
        response.raise_for_status()
        data = response.json()

        access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)

        self.token_info = {
            "access_token": access_token,
            "expires_at": time.time() + expires_in,
        }
        self._save_token_cache(self.token_info)
        logger.info("✅ Token fetched and cached.")
        return access_token
