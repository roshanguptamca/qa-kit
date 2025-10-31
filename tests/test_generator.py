import pytest
from qa_kit.generator import TestGenerator

def test_generator_writes_files(tmp_path):
    spec = {
        "name": "x",
        "base_url": "http://localhost:8000",
        "tests": [
            {
                "id": "t1",
                "name": "one",
                "method": "GET",
                "path": "/",
                "params": {},
                "body": None,
                "expected": {"status_code": 200},
            }
        ],
    }
    out_dir = tmp_path / "generated"
    gen = TestGenerator(spec, out_dir=out_dir)
    files = gen.generate()
    assert len(files) == 1
    assert (out_dir / "test_t1.py").exists()