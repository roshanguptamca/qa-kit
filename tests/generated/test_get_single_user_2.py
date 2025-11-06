import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "https://reqres.in/api"


@allure.story("ReqRes API Suite")
async def test_get_single_user_get_single_user():
    """get_single_user"""
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers={"X-Test-Header": "MyHeaderValue"}, verify=SSL_VERIFY
    ) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "GET", "/users/2", json={}, params={}, timeout=10
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == 200
    _assert_partial(
        {"data": {"id": 2}},
        resp.json(),
        ignore_keys=["data.email", "data.first_name", "data.last_name", "data.avatar"],
        use_wildcard=False,
    )
