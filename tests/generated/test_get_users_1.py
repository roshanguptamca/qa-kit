import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "https://reqres.in/api"


@allure.story("ReqRes API Suite")
async def test_get_users_get_users():
    """get_users"""
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers={"X-Test-Header": "MyHeaderValue"}, verify=SSL_VERIFY
    ) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "GET", "/users", json={}, params={"page": 2}, timeout=10
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == 200
    _assert_partial(
        {"page": 2}, resp.json(), ignore_keys=["data", "support"], use_wildcard=False
    )
