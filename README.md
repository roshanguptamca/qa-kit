# QA-Kit

**QA-Kit** is a CLI and test generator for REST API integration tests using **pytest** and **httpx**, with built-in support for **Allure reporting**. Generate tests from JSON specifications, run them asynchronously, and generate detailed HTML reports.

---
## Documentation

For detailed usage instructions, CI/CD examples, and setup guide, see the full documentation:

[QA-Kit User Guide (Google Docs)](https://docs.google.com/document/d/10j6AAWTP2WhPDghi9L3MmLJgjmWtkbnyXdMrW6Do1MI/edit?usp=sharing)

# Allure Report 
https://roshanguptamca.github.io/qa-kit/ 

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
   
   # Dry-run / verbose only
    qa_kit generate tests/specs --verbose --dry
    
    # Actual generation with delta
    qa_kit generate tests/specs --delta --verbose

    qa_kit generate tests/specs/ --verbose

    # Generate only changed/new tests
    qa_kit generate tests/specs/ --verbose --delta

    # Delta mode + cleanup obsolete
    qa_kit generate tests/specs/ --verbose --delta --clean-removed
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

# QA-Kit Roadmap:
#### OpenAPI / Swagger Spec Support
     Input: JSON/YAML OpenAPI spec
     Output: Auto-generated async pytest tests
     Optional: Generate default request bodies based on schema
### Parametrized & Data-Driven Tests
    Support for multiple test cases from JSON, CSV, or Excel
    Generate @pytest.mark.parametrize automatically
### AI-Assisted Test Generation
#### Focus: Help users automatically generate tests based on API specs or historical data.

Features:
    Smart test generation:
    
        Suggest additional test cases (edge cases, missing inputs) based on spec analysis.
        
        Automatically generate negative test scenarios (invalid payloads, bad params).
        
        AI-based validation hints:
        
        Suggest keys to ignore or fields to focus on in assertions.
        
        Integration with OpenAI / local LLM:
        
        Generate descriptive docstrings for tests.
        
        Provide inline suggestions for improving test coverage.

    Example CLI:
        qa_kit --ai-assist --spec api_spec.json --output tests/generated
        qa_kit --ai-assist--test tests/generated/test_api.py
### AI-Powered Test Optimization
#### Features:

    Test suite prioritization:
        Rank tests based on likelihood of failure, coverage gaps, or historical flakiness.
        Duplicate test detection:
        Automatically detect overlapping or redundant tests and suggest merges.
        Response anomaly detection:
        Use AI to detect unusual response patterns in API results, highlighting potential bugs.
### AI-Driven Reporting & Analysis
#### Features:
    Smart report summaries:
        Auto-generate concise human-readable summaries for QA/management.
        Trend analysis:
            Predict potential failure trends across builds or releases using historical data.
            Code & spec improvement suggestions:
            Suggest changes to API specs or test payloads based on AI analysis of failed tests.
        Example Output:
            Highlight which endpoints are high-risk
            Predict areas with insufficient test coverage
            Suggest new tests for endpoints with historical instability
### Fully Autonomous Test Assistant
#### Features:
    Continuous learning:
        Autonomous test suite maintenance:
            Automatically updates or generates new tests for spec changes.
        Auto-fix broken tests:
            Proposes corrections for failing tests due to schema changes or new endpoints.
        Natural language interface:
            Users can describe tests in plain English; AI converts to pytest tests.
        Example CLI:
           qa_kit ai --describe "Test user creation with invalid email" --generate

### CLI Enhancements
    qa_kit validate-spec → check spec file validity
     qa_kit diff-tests → compare generated tests with previous versions
     Improved qa_kit clean → safely clean tests and reports

### Improved Report Handling
    Auto-generate Allure reports if results exist
    Option to publish HTML to GitHub Pages
    Add trend charts and summary tables in the report

#### Better Async Framework Support
     Support for aiohttp + optional sync mode with requests
     Users can choose framework via CLI flags
### CI/CD Integration
    Predefined GitHub Actions, GitLab CI, and Jenkins pipelines
    Docker-ready templates for isolated test runs
    Postman / HAR Import
    Import Postman collections / HAR files as JSON specs
### Generate tests automatically
    Mock Server / Sandbox Mode
    Optional mock server for testing without live APIs
    Record & replay responses
### Soft Assertions
    Allow multiple assertion failures in one test run
    Configurable via CLI flags
### Advanced Reporting & Extensibility
    Plugin System
        Users can write plugins for custom generators, validators, or reporters
        Simple interface to extend functionality
    Enhanced Reports
        PDF export of Allure results
        Include request/response snapshots
        Visual trend charts for API performance
    Pre/Post Test Hooks
        Users can define setup/teardown hooks for each test or suite
        Ideal for authentication, DB reset, or test data setup
### Production-Ready Ecosystem
    Packaging & Distribution
        Publish to PyPI for easy installation
        Docker images for isolated environments
    Comprehensive Documentation
        User guide, API reference, and examples
        Tutorials for common use cases
    Community & Support
        Dedicated forum or Discord for user support
        Regular updates and maintenance

# License 
MIT © RoshanGupta





