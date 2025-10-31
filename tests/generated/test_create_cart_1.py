import pytest
import httpx
import allure

@allure.story("Cart API Suite")
@pytest.mark.asyncio
async def test_create_cart():
    """create_cart"""
    async with httpx.AsyncClient(base_url="https://api.acc.kpn.org/shop-core/v1") as client:
        resp = await client.request(
            "POST",
            "/cart/",
            json={
    "channel": {
        "id": "bo_lov_saleschannel_online",
        "name": "Online"
    },
    "marketSegment": {
        "id": "bo_lov_marketsegment_consumer",
        "name": "Consumer"
    }
},
            params={}
        )
        assert resp.status_code == 200
        assert resp.json() == {
    "status": "ACTIVE",
    "channel": {
        "id": "bo_lov_saleschannel_online",
        "name": "Online"
    },
    "market_segment": {
        "id": "bo_lov_marketsegment_consumer",
        "name": "Consumer"
    }
}
