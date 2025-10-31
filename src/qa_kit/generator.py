import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TestGenerator:
    """
    Generates pytest test files from a validated JSON API spec.
    """

    def __init__(self, spec_data: Dict[str, Any], out_dir: str = "tests/generated"):
        self.spec_data = spec_data
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = spec_data.get("base_url", "http://localhost:8000")
        self.suite_name = spec_data.get("name", "API Suite")

    def generate(self) -> list[Path]:
        """
        Generate test files for all tests in spec_data['tests'].
        Returns a list of generated file paths.
        """
        files = []
        for i, test in enumerate(self.spec_data["tests"], 1):
            file_path = self.out_dir / f"test_{test['name'].lower()}_{i}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._generate_test_content(test))
            files.append(file_path)
            logger.info("Generated test file: %s", file_path)
        return files

    def _generate_test_content(self, test: Dict[str, Any]) -> str:
        """
        Returns the Python content of a single pytest file for a test.
        Uses httpx.AsyncClient for async requests and Allure annotations.
        """
        method = test["method"].upper()
        path = test["path"]
        body = test.get("body", {})
        params = test.get("params", {})
        expected = test["expected"]
        expected_status = expected.get("status_code", 200)
        expected_json = expected.get("json", {})

        # Ensure JSON formatting for dicts
        import json
        body_str = json.dumps(body, indent=4)
        params_str = json.dumps(params, indent=4)
        expected_json_str = json.dumps(expected_json, indent=4)

        return f"""import pytest
import httpx
import allure

@allure.story("{self.suite_name}")
@pytest.mark.asyncio
async def test_{test['name'].lower()}():
    \"\"\"{test.get('description', test['name'])}\"\"\"
    async with httpx.AsyncClient(base_url="{self.base_url}") as client:
        resp = await client.request(
            "{method}",
            "{path}",
            json={body_str},
            params={params_str}
        )
        assert resp.status_code == {expected_status}
        assert resp.json() == {expected_json_str}
"""

