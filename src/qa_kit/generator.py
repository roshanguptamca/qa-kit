import logging
from pathlib import Path
from typing import Dict, Any, List
import json
import os

logger = logging.getLogger(__name__)


class TestGenerator:
    """
    Generates pytest test files from a validated JSON API spec.
    Supports async httpx requests, partial JSON assertions, ignored keys, and wildcard matching.
    """

    def __init__(self, spec_data: Dict[str, Any], out_dir: str = "tests/generated"):
        self.spec_data = spec_data
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = spec_data.get("base_url", "http://localhost:8000")
        self.suite_name = spec_data.get("name", "API Suite")
        self._ensure_helpers()

    def _ensure_helpers(self):
        """
        Create a helper module with _assert_partial, SSL_VERIFY, and pytestmark.
        """
        utils_dir = Path("tests/utils")
        utils_dir.mkdir(parents=True, exist_ok=True)
        helper_path = utils_dir / "test_helpers.py"

        helper_code = (
            "import os\n"
            "import pytest\n"
            "import fnmatch\n\n"
            "# Module-level async marker for pytest\n"
            "pytestmark = pytest.mark.asyncio\n\n"
            "# SSL verification from environment (default False)\n"
            "SSL_VERIFY = os.getenv('QA_KIT_SSL_VERIFY', 'false').lower() not in ('0', 'false', 'no')\n\n"
            "def _path_matches_any(path: str, patterns: list[str], use_wildcard: bool) -> bool:\n"
            "    for pat in patterns or []:\n"
            "        if use_wildcard:\n"
            "            if fnmatch.fnmatch(path, pat):\n"
            "                return True\n"
            "        else:\n"
            "            if path == pat or path.startswith(pat + '.'):\n"
            "                return True\n"
            "    return False\n\n"
            "def _assert_partial(expected, actual, path='', ignore_keys=None, use_wildcard=False):\n"
            "    ignore_keys = ignore_keys or []\n"
            "    if isinstance(expected, dict):\n"
            "        assert isinstance(actual, dict), f'Type mismatch at {path}: expected dict, got {type(actual)}'\n"
            "        for k, v in expected.items():\n"
            "            new_path = f'{path}.{k}' if path else k\n"
            "            if _path_matches_any(new_path, ignore_keys, use_wildcard):\n"
            "                continue\n"
            "            assert k in actual, f'Missing key: {new_path}'\n"
            "            _assert_partial(v, actual[k], new_path, ignore_keys, use_wildcard)\n"
            "    elif isinstance(expected, list):\n"
            "        assert isinstance(actual, list), f'Type mismatch at {path}: expected list, got {type(actual)}'\n"
            "        assert len(actual) >= len(expected), f'List too short at {path}: expected ≥{len(expected)} items'\n"
            "        for i, v in enumerate(expected):\n"
            "            _assert_partial(v, actual[i], f'{path}[{i}]', ignore_keys, use_wildcard)\n"
            "    else:\n"
            "        if _path_matches_any(path, ignore_keys, use_wildcard):\n"
            "            return\n"
            "        assert expected == actual, f'Value mismatch at {path}: expected={expected}, actual={actual}'\n"
        )

        if not helper_path.exists() or helper_path.read_text() != helper_code:
            helper_path.write_text(helper_code)
            logger.info(f"✅ Helper file created/updated: {helper_path}")

    def generate(self) -> List[Path]:
        """
        Generate pytest test files from the JSON spec.
        Returns a list of generated file paths.
        """
        files = []
        for i, test in enumerate(self.spec_data.get("tests", []), 1):
            safe_name = test["name"].lower().replace("-", "_")
            file_path = self.out_dir / f"test_{safe_name}_{i}.py"
            file_path.write_text(self._generate_test_content(test, i))
            files.append(file_path)
            logger.info(f"🧾 Generated: {file_path}")
        return files

    def _generate_test_content(self, test: Dict[str, Any], index: int) -> str:
        """
        Build the Python test file content for a single test.
        """
        method = test["method"].upper()
        path = test["path"]
        body_str = json.dumps(test.get("body", {}), indent=4)
        params_str = json.dumps(test.get("params", {}), indent=4)
        expected_status = test.get("expected", {}).get("status_code", 200)
        expected_json = test.get("expected", {}).get("json", {})
        expected_json_str = json.dumps(expected_json, indent=4)

        ignore_assert = test.get("ignore_assert", False)
        ignore_json = test.get("ignore_json", [])
        use_wildcard = test.get("use_wildcard", False)

        test_id = test.get("id", f"{test['name']}_{index}").replace("-", "_")
        test_name = test["name"].lower().replace("-", "_")
        description = test.get("description", test["name"])

        if ignore_assert:
            assertion_block = "    # JSON validation skipped"
        else:
            assertion_block = (
                f"    _assert_partial({expected_json_str}, resp.json(), "
                f"ignore_keys={ignore_json}, use_wildcard={use_wildcard})"
            )

        # ✅ Build the test content
        content = f"""\
import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark

BASE_URL = "{self.base_url}"

@allure.story("{self.suite_name}")
async def test_{test_name}_{test_id}():
    \"\"\"{description}\"\"\"
    async with httpx.AsyncClient(base_url=BASE_URL, verify=SSL_VERIFY) as client:
        resp = await client.request(
            "{method}",
            "{path}",
            json={body_str},
            params={params_str}
        )

    assert resp.status_code == {expected_status}
{assertion_block}
"""
        return content.strip() + "\n"
