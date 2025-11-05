import pytest
import json
from pathlib import Path
from qa_kit.generator import TestGenerator


def test_generator_creates_test_file(tmp_path):
    # Sample JSON spec
    sample_spec = {
        "name": "Sample API Suite",
        "base_url": "https://jsonplaceholder.typicode.com",
        "tests": [
            {
                "name": "get_post",
                "method": "GET",
                "path": "/posts/1",
                "expected": {"status_code": 200, "json": {"userId": 1, "id": 1}},
                "ignore_assert": False,
                "ignore_json": [],
                "use_wildcard": False,
            }
        ],
    }

    # Output directory
    out_dir = tmp_path / "generated_tests"

    # Initialize generator
    generator = TestGenerator(sample_spec, out_dir=str(out_dir))
    generated_files = generator.generate()

    # Check a file was generated
    assert len(generated_files) == 1
    test_file = generated_files[0]
    assert test_file.exists()

    # Verify content includes expected pieces
    content = test_file.read_text()
    assert "async def test_get_post_get_post_1()" in content
    assert "await client.request(" in content
    assert "_assert_partial" in content
    assert 'BASE_URL = "https://jsonplaceholder.typicode.com"' in content
