import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark

BASE_URL = "https://jsonplaceholder.typicode.com"

@allure.story("JSONPlaceholder API Suite")
async def test_create_post_create_post():
    """create_post"""
    async with httpx.AsyncClient(base_url=BASE_URL, verify=SSL_VERIFY) as client:
        resp = await client.request(
            "POST",
            "/posts",
            json={
    "title": "foo",
    "body": "bar",
    "userId": 1
},
            params={}
        )

    assert resp.status_code == 201
    _assert_partial({
    "title": "foo",
    "body": "bar",
    "userId": 1
}, resp.json(), ignore_keys=[], use_wildcard=False)
