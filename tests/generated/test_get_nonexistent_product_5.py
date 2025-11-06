import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "https://dummyjson.com"


@allure.story("DummyJSON API Suite")
async def test_get_nonexistent_product_get_nonexistent_product():
    """get_nonexistent_product"""
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers={}, verify=SSL_VERIFY
    ) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "GET", "/products/999999", json={}, params={}, timeout=10
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == 404
    _assert_partial({}, resp.json(), ignore_keys=[], use_wildcard=False)
