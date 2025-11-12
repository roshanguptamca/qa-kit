import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import hashlib
import typer
import asyncio
import httpx
import os

from .client import OAuth2Client  # Make sure client.py provides OAuth2Client

logger = logging.getLogger(__name__)


class TestGenerator:
    """
    Generates pytest test files from a validated JSON API spec.

    Features:
    - Async httpx requests with retries
    - Partial JSON assertions with wildcard & ignore keys
    - Delta generation
    - Obsolete test cleanup
    - Custom headers support
    - OAuth2 Bearer token injection via client.py
    - Colored CLI output
    - Dry-run mode (show what would be created/updated)
    """

    CACHE_FILE = ".qa_cache.json"

    def __init__(
        self,
        spec_data: Dict[str, Any],
        out_dir: str = "tests/generated",
        delta_mode: bool = False,
        clean_removed: bool = False,
        verbose: bool = False,
        oauth_client: Optional[OAuth2Client] = None,
    ):
        self.spec_data = spec_data
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = spec_data.get("base_url", "http://localhost:8000")
        self.suite_name = spec_data.get("name", "API Suite")
        self.verbose = verbose
        self.delta_mode = delta_mode
        self.clean_removed = clean_removed

        # ---------------- Auto-create OAuth client if needed ---------------- #
        self.oauth_client = oauth_client
        if not self.oauth_client:
            for test in spec_data.get("tests", []):
                if test.get("use_oauth"):
                    token_url = os.getenv("QA_TOKEN_URL")
                    client_id = os.getenv("QA_CLIENT_ID")
                    client_secret = os.getenv("QA_CLIENT_SECRET")
                    scope = os.getenv("QA_SCOPE")

                    if not token_url or not client_id or not client_secret:
                        raise ValueError(
                            "Environment variables QA_TOKEN_URL, QA_CLIENT_ID, QA_CLIENT_SECRET must be set for OAuth"
                        )

                    self.oauth_client = OAuth2Client(
                        token_url=token_url,
                        client_id=client_id,
                        client_secret=client_secret,
                        scope=scope,
                    )
                    if self.verbose:
                        typer.secho(
                            "🔑 OAuth2Client automatically created",
                            fg=typer.colors.CYAN,
                        )
                    break

        self._ensure_helpers()
        self.cache = self._load_cache()

    # ---------------- Cache Management ---------------- #

    def _load_cache(self) -> Dict[str, Any]:
        if Path(self.CACHE_FILE).exists():
            try:
                return json.loads(Path(self.CACHE_FILE).read_text())
            except Exception:
                logger.warning("⚠️ Cache file is corrupt, recreating it.")
        return {}

    def _save_cache(self):
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"💥 Failed to save cache: {e}")

    def _compute_hash(self, test: Dict[str, Any]) -> str:
        return hashlib.md5(json.dumps(test, sort_keys=True).encode()).hexdigest()

    # ---------------- Helper Management ---------------- #

    def _ensure_helpers(self):
        utils_dir = Path("tests/utils")
        utils_dir.mkdir(parents=True, exist_ok=True)
        helper_path = utils_dir / "test_helpers.py"

        helper_code = (
            "import os\n"
            "import pytest\n"
            "import fnmatch\n\n"
            "pytestmark = pytest.mark.asyncio\n\n"
            "SSL_VERIFY = os.getenv('QA_KIT_SSL_VERIFY','false').lower() not in ('0','false','no')\n\n"
            "def _path_matches_any(path:str,patterns:list[str],use_wildcard:bool)->bool:\n"
            "    for pat in patterns or []:\n"
            "        if use_wildcard and fnmatch.fnmatch(path,pat): return True\n"
            "        elif path==pat or path.startswith(pat+'.'): return True\n"
            "    return False\n\n"
            "def _assert_partial(expected, actual, path='', ignore_keys=None, use_wildcard=False):\n"
            "    ignore_keys = ignore_keys or []\n"
            "    if isinstance(expected, dict):\n"
            "        assert isinstance(actual,dict),f'Type mismatch at {path}: expected dict, got {type(actual)}'\n"
            "        for k,v in expected.items():\n"
            "            new_path=f'{path}.{k}' if path else k\n"
            "            if _path_matches_any(new_path,ignore_keys,use_wildcard): continue\n"
            "            assert k in actual,f'Missing key: {new_path}'\n"
            "            _assert_partial(v,actual[k],new_path,ignore_keys,use_wildcard)\n"
            "    elif isinstance(expected,list):\n"
            "        assert isinstance(actual,list),f'Type mismatch at {path}: expected list, got {type(actual)}'\n"
            "        assert len(actual)>=len(expected),f'List too short at {path}: expected ≥{len(expected)} items'\n"
            "        for i,v in enumerate(expected): _assert_partial(v,actual[i],f'{path}[{i}]',ignore_keys,use_wildcard)\n"
            "    else:\n"
            "        if _path_matches_any(path,ignore_keys,use_wildcard): return\n"
            "        assert expected==actual,f'Value mismatch at {path}: expected={expected}, actual={actual}'\n"
        )

        if not helper_path.exists() or helper_path.read_text() != helper_code:
            helper_path.write_text(helper_code)
            logger.info(f"✅ Helper file created/updated: {helper_path}")

    # ---------------- Test Generation ---------------- #

    def generate(
        self, delta: bool = None, clean_removed: bool = None, dry_run: bool = False
    ) -> List[Path]:
        if delta is not None:
            self.delta_mode = delta
        if clean_removed is not None:
            self.clean_removed = clean_removed

        files: List[Path] = []
        current_ids = set()
        changes = 0
        tests = self.spec_data.get("tests", [])

        if not tests:
            typer.secho(
                "⚙️ No tests found in spec — nothing to generate.",
                fg=typer.colors.BRIGHT_BLACK,
            )
            return []

        for i, test in enumerate(tests, 1):
            test_id = test.get("id") or f"{test['name']}_{i}"
            safe_name = test["name"].lower().replace("-", "_")
            file_path = self.out_dir / f"test_{safe_name}_{i}.py"

            new_hash = self._compute_hash(test)
            current_ids.add(test_id)
            cached = self.cache.get(test_id)
            old_hash = cached["hash"] if cached else None
            new_content = self._generate_test_content(test, i)

            # Determine action for dry-run
            if cached and old_hash == new_hash and file_path.exists():
                action = "skipped (unchanged)"
            elif file_path.exists() and file_path.read_text() == new_content:
                action = "skipped (no content change)"
            elif cached:
                action = "would update"
            else:
                action = "would create"

            if dry_run or self.verbose:
                typer.secho(f"⚪ {action}: {file_path}", fg=typer.colors.BRIGHT_BLACK)
                if dry_run:
                    continue  # do not write files in dry-run

            # Normal generation
            file_path.write_text(new_content)
            self.cache[test_id] = {"hash": new_hash, "file": str(file_path)}
            files.append(file_path)
            changes += 1

            if self.verbose and not dry_run:
                typer.secho(
                    f"{'🔄 Updated' if cached else '🆕 Created'}: {file_path}",
                    fg=typer.colors.GREEN if not cached else typer.colors.YELLOW,
                )

        # Clean removed
        if self.clean_removed and not dry_run:
            removed = [tid for tid in list(self.cache.keys()) if tid not in current_ids]
            for tid in removed:
                old_path = Path(self.cache[tid]["file"])
                if old_path.exists():
                    old_path.unlink()
                    if self.verbose:
                        typer.secho(
                            f"🗑️ Removed obsolete test: {old_path}", fg=typer.colors.RED
                        )
                del self.cache[tid]

        if not dry_run:
            self._save_cache()
            if changes == 0:
                typer.secho(
                    "⚙️ Nothing found to generate — all tests are up to date.",
                    fg=typer.colors.BRIGHT_BLACK,
                )
            else:
                typer.secho(
                    f"✅ Generated or updated {changes} test file(s) in {self.out_dir}",
                    fg=typer.colors.GREEN,
                )

        return files

    # ---------------- Test File Builder ---------------- #

    def _generate_test_content(self, test: Dict[str, Any], index: int) -> str:
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

        # Merge headers
        headers = test.get("headers", {})
        if test.get("use_oauth") and self.oauth_client:
            token = self.oauth_client.get_token()
            headers["Authorization"] = f"Bearer {token}"
        headers_str = json.dumps(headers, indent=4)

        test_id = test.get("id", f"{test['name']}_{index}").replace("-", "_")
        test_name = test["name"].lower().replace("-", "_")
        description = test.get("description", test["name"])

        assertion_block = (
            "    # JSON validation skipped"
            if ignore_assert
            else f"    _assert_partial({expected_json_str}, resp.json(), ignore_keys={ignore_json}, use_wildcard={use_wildcard})"
        )

        return (
            f"""\
import pytest
import allure
import httpx
from tests.utils.test_helpers import _assert_partial, SSL_VERIFY, pytestmark
import asyncio

BASE_URL = "{self.base_url}"

@allure.story("{self.suite_name}")
async def test_{test_name}_{test_id}():
    \"\"\"{description}\"\"\"
    async with httpx.AsyncClient(base_url=BASE_URL, headers={headers_str}, verify=SSL_VERIFY) as client:
        # Automatic retries for request
        for attempt in range(3):
            try:
                resp = await client.request(
                    "{method}",
                    "{path}",
                    json={body_str},
                    params={params_str},
                    timeout=10
                )
                break
            except httpx.RequestError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

    assert resp.status_code == {expected_status}
{assertion_block}
""".strip()
            + "\n"
        )
