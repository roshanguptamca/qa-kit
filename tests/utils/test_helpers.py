import os
import pytest
import fnmatch

pytestmark = pytest.mark.asyncio

SSL_VERIFY = os.getenv("QA_KIT_SSL_VERIFY", "false").lower() not in ("0", "false", "no")


def _path_matches_any(path: str, patterns: list[str], use_wildcard: bool) -> bool:
    for pat in patterns or []:
        if use_wildcard and fnmatch.fnmatch(path, pat):
            return True
        elif path == pat or path.startswith(pat + "."):
            return True
    return False


def _assert_partial(expected, actual, path="", ignore_keys=None, use_wildcard=False):
    ignore_keys = ignore_keys or []
    if isinstance(expected, dict):
        assert isinstance(
            actual, dict
        ), f"Type mismatch at {path}: expected dict, got {type(actual)}"
        for k, v in expected.items():
            new_path = f"{path}.{k}" if path else k
            if _path_matches_any(new_path, ignore_keys, use_wildcard):
                continue
            assert k in actual, f"Missing key: {new_path}"
            _assert_partial(v, actual[k], new_path, ignore_keys, use_wildcard)
    elif isinstance(expected, list):
        assert isinstance(
            actual, list
        ), f"Type mismatch at {path}: expected list, got {type(actual)}"
        assert len(actual) >= len(
            expected
        ), f"List too short at {path}: expected ≥{len(expected)} items"
        for i, v in enumerate(expected):
            _assert_partial(v, actual[i], f"{path}[{i}]", ignore_keys, use_wildcard)
    else:
        if _path_matches_any(path, ignore_keys, use_wildcard):
            return
        assert (
            expected == actual
        ), f"Value mismatch at {path}: expected={expected}, actual={actual}"
