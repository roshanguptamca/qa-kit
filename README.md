# QA-Kit

**QA-Kit** is a CLI and test generator for REST API integration tests using **pytest** and **httpx**, with built-in support for **Allure reporting**. Generate tests from JSON specifications, run them asynchronously, and generate detailed HTML reports.

---

## Features

- Generate `pytest` tests from JSON API specifications
- Async HTTP requests with `httpx`
- Partial JSON assertions with recursive key ignore support
- Optional wildcard matching for ignored keys
- Global option to skip assertions
- Allure reporting support (HTML reports)
- Fully configurable via environment variables
- CLI for generation, running, linting, and reporting
- Production-ready and PyPI compatible

---

## Installation
### 1. Clone the repository
```bash
git clone https://github.com/roshanguptamca/qa-kit.git
cd qa-kit
```
### Install Python dependencies (recommended via Poetry)

```bash 
poetry install
```
### Install Allure CLI (required for HTML reports)
macOS (Homebrew):
```bash 
brew install allure
```

Linux (Debian/Ubuntu):
```bash 
sudo apt-add-repository ppa:qameta/allure
sudo apt update
sudo apt install allure

```
Windows (via Scoop):
```bash 
scoop install allure
```

Verify installation:
```bash 
allure --version
````

⚠️ QA-Kit will fail to generate HTML reports without the Allure CLI.

4. (Optional) Docker

If you prefer, Allure reports can also be generated via Docker:
```bash 
docker run --rm -v $(pwd)/allure-results:/allure-results -v $(pwd)/allure-report:/allure
```

# Quick Start
```bash
pip install qa-kit


Or install from GitHub:

```bash
pip install git+https://github.com/roshanguptamca/qa-kit.git
```

1. Prepare JSON specs
    Example: tests/specs/cart_api.json:
        ```json```
        {
          "name": "Cart API Suite",
          "base_url": "https://api.example.com",
          "tests": [
            {
              "id": "create-cart-1",
              "name": "create_cart",
              "method": "POST",
              "path": "/cart/",
              "body": {
                "channel": {"id": "online", "name": "Online"}
              },
              "expected": {
                "status_code": 200,
                "json": {
                  "status": "ACTIVE",
                  "channel": {"id": "online"}
                }
              }
            }
          ]
        }

        ```
2. Generate tests
    ```bash 
   qa_kit generate tests/specs/cart_api.json -o tests/generated
    ```
3. Run tests with Allure reporting
    ```bash` qa_kit run -t tests/generated
    ``````
4. Generate Allure report
    ```bash
   qa_kit report -o allure-report
    ```     
 This runs tests and generates results in allure-results. You can then open the report:
    ```bash
   qa_kit open
    ```
# Environment Variables
- `QA_KIT_SSL_VERIFY`: Set to `true` to enable SSL verification (default: `false`)
- `USE_WILDCARD`: Set to `true` to enable wildcard matching for ignored keys (default: `false`)
- `IGNORE_ASSERT` : Set to `true` to skip JSON assertions (default: `false`)

# JSON Spec Options:

| Field                  | Description                                      |
| ---------------------- | ------------------------------------------------ |
| `id`                   | Unique test identifier                           |
| `name`                 | Test name                                        |
| `method`               | HTTP method (`GET`, `POST`, etc.)                |
| `path`                 | Endpoint path                                    |
| `body`                 | JSON body for request                            |
| `params`               | Query parameters                                 |
| `expected.status_code` | Expected HTTP status code                        |
| `expected.json`        | Expected JSON response                           |
| `ignore_assert`        | Skip JSON assertions for this test               |
| `ignore_json`          | List of keys to ignore recursively in assertions |
| `use_wildcard`         | Enable wildcard for ignored keys                 |


# Example Generated Test:
```python
import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY

BASE_URL = "https://jsonplaceholder.typicode.com"

@allure.story("JSONPlaceholder API Suite")
async def test_get_post_1_get_post_1():
    """get_post_1"""
    async with httpx.AsyncClient(base_url=BASE_URL, verify=SSL_VERIFY) as client:
        resp = await client.request(
            "GET",
            "/posts/1",
            json={},
            params={}
        )

    assert resp.status_code == 200
    _assert_partial({
        "userId": 1,
        "id": 1
    }, resp.json(), ignore_keys=[], use_wildcard=False)
```


# Example:
# Project Structure
```
tests/
├── specs/         # JSON API specs
├── generated/     # Generated tests
└── utils/
    └── test_helpers.py  # Shared helpers

```
# Contributing

Contributions welcome! Please fork, create a branch, and submit PRs.
Follow black, isort, and flake8 for code formatting and linting.

# License 
MIT © RoshanGupta





