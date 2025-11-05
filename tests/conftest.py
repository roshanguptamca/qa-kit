import os
import pytest
import pytest_asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def base_url():
    return os.getenv("API_BASE_URL", "https://api.acc.kpn.org/shop-core/v1")

@pytest.fixture(scope="session")
def ssl_verify():
    """
    Control SSL verification:
    - True (default) -> verify certificates
    - False -> disable verification
    Can also provide path to CA bundle.
    """
    val = os.getenv("QA_SSL_VERIFY", "false").lower()
    if val in ["false", "0", "no"]:
        return False
    return True

@pytest_asyncio.fixture
async def client(base_url, ssl_verify):
    async with httpx.AsyncClient(base_url=base_url, verify=ssl_verify, timeout=10.0) as c:
        yield c
