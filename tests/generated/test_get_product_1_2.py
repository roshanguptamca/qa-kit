import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "https://dummyjson.com"


@allure.story("DummyJSON API Suite")
async def test_get_product_1_get_product_1():
    """get_product_1"""
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers={}, verify=SSL_VERIFY
    ) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "GET", "/products/1", json={}, params={}, timeout=10
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == 200
    _assert_partial(
        {"id": 1},
        resp.json(),
        ignore_keys=[
            "title",
            "description",
            "price",
            "brand",
            "thumbnail",
            "images",
            "stock",
            "category",
        ],
        use_wildcard=False,
    )
