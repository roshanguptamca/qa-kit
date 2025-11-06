import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "https://dummyjson.com"


@allure.story("DummyJSON API Suite")
async def test_create_product_create_product():
    """create_product"""
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers={}, verify=SSL_VERIFY
    ) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "POST",
                    "/products/add",
                    json={"title": "QA Kit Test Product"},
                    params={},
                    timeout=10,
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == 201
    _assert_partial(
        {"title": "QA Kit Test Product"},
        resp.json(),
        ignore_keys=["id"],
        use_wildcard=False,
    )
