import subprocess
import sys
import os
import webbrowser
from pathlib import Path
import logging
import pytest

logger = logging.getLogger(__name__)

def run_pytest(
    test_path: str,
    extra_args: list[str] = None,
    allure_dir: str = "allure-results",
    open_report: bool = False,
    ssl_verify: bool = True
) -> int:
    """
    Run pytest programmatically with Allure results.
    Supports optional SSL verification and HTML report via Docker.

    Args:
        test_path: Path to generated test files.
        extra_args: Additional pytest CLI arguments.
        allure_dir: Directory to store Allure results.
        open_report: Whether to generate and open HTML report.
        ssl_verify: Whether to verify SSL certificates.

    Returns:
        int: pytest exit code.
    """
    extra_args = extra_args or []

    # SSL verification via env
    if not ssl_verify:
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        logger.info("⚠️ SSL verification disabled")

    pytest_args = [test_path, "-q"] + extra_args
    logger.info(f"Running pytest: {pytest_args}")
    exit_code = pytest.main(pytest_args)

    if open_report:
        generate_allure_html(allure_dir)

    return exit_code


def generate_allure_html(allure_dir: str = "allure-results", report_dir: str = "allure-report"):
    """
    Generate Allure HTML report using Docker.
    Requires Docker installed.

    Args:
        allure_dir: Directory containing Allure raw results.
        report_dir: Directory to generate HTML report.
    """
    results = Path(allure_dir)
    report = Path(report_dir)
    report.mkdir(parents=True, exist_ok=True)

    if not results.exists() or not any(results.iterdir()):
        logger.warning("⚠️ Allure results directory is empty: %s", results)
        return

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{results.absolute()}:/allure-results",
        "-v", f"{report.absolute()}:/allure-report",
        "allure/allure", "generate", "/allure-results",
        "-o", "/allure-report", "--clean"
    ]

    try:
        logger.info("📊 Generating Allure HTML report via Docker...")
        subprocess.run(docker_cmd, check=True)
        index_file = report / "index.html"
        if index_file.exists():
            webbrowser.open(index_file.as_uri())
            logger.info(f"✅ Allure HTML report opened at {index_file}")
        else:
            logger.warning("⚠️ Allure HTML report generation failed.")
    except FileNotFoundError:
        logger.warning("⚠️ Docker not found. Install Docker to generate Allure HTML reports.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to generate Allure report: {e}")
