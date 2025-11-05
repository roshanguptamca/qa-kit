import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark

BASE_URL = "https://jsonplaceholder.typicode.com"

@allure.story("JSONPlaceholder API Suite")
async def test_get_posts_get_posts():
    """get_posts"""
    async with httpx.AsyncClient(base_url=BASE_URL, verify=SSL_VERIFY) as client:
        resp = await client.request(
            "GET",
            "/posts",
            json={},
            params={}
        )

    assert resp.status_code == 200
    _assert_partial([
    {
        "userId": 1,
        "id": 1
    }
], resp.json(), ignore_keys=['title', 'body'], use_wildcard=False)
