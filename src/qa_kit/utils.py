import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def load_json(path: str) -> Dict[str, Any]:
    """
    Load and validate the input JSON spec file.

    Expected top-level format (example in tests/sample_specs/api_spec.json):
    {
        "name": "Sample API Suite",
        "base_url": "http://localhost:8000",
        "tests": [
            {
                "id": "health-1",
                "name": "healthcheck",
                "method": "GET",
                "path": "/health",
                "params": {},
                "body": null,
                "expected": {
                    "status_code": 200,
                    "json": {"status": "ok"}
                }
            }
        ]
    }

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If required keys are missing or invalid.
    """
    spec_path = Path(path)
    if not spec_path.exists():
        logger.error("Spec file not found: %s", path)
        raise FileNotFoundError(f"Spec file not found: {path}")

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Spec file is not valid JSON: %s", path)
        raise e

    # Basic validation
    if "tests" not in data or not isinstance(data["tests"], list):
        raise ValueError("Spec JSON must contain a 'tests' list")

    for i, test in enumerate(data["tests"], 1):
        required_keys = {"id", "name", "method", "path", "expected"}
        missing = required_keys - test.keys()
        if missing:
            raise ValueError(f"Test #{i} is missing required keys: {missing}")

        if "status_code" not in test["expected"]:
            raise ValueError(f"Test #{i} expected field must contain 'status_code'")

    logger.info("Loaded JSON spec successfully: %s", path)
    return data
