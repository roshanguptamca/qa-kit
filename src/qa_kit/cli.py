import logging
from pathlib import Path
import typer
import sys
import os

from qa_kit.utils import load_json
from qa_kit.generator import TestGenerator
from qa_kit.runner import run_pytest

app = typer.Typer(help="QA-Kit: Generate and run API integration tests from JSON specs.")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@app.command()
def generate(
    spec: str = typer.Argument(..., help="Path to JSON spec file describing APIs and expected responses."),
    out: str = typer.Option("tests/generated", "--out", "-o", help="Output directory for generated pytest files."),
):
    """
    Generate pytest test files from a JSON spec definition.
    """
    try:
        spec_path = Path(spec)
        if not spec_path.exists():
            logger.error(f"❌ Spec file not found: {spec_path}")
            raise typer.Exit(code=2)

        logger.info(f"📄 Loading API spec from: {spec_path}")
        data = load_json(str(spec_path))

        generator = TestGenerator(data, out_dir=out)
        files = generator.generate()

        logger.info(f"✅ Generated {len(files)} test file(s) in {out}")
        typer.echo(f"Generated {len(files)} test file(s) in {out}")

    except Exception as e:
        logger.exception("💥 Error generating test files")
        raise typer.Exit(code=1) from e


@app.command()
def run(
    spec: str = typer.Option(None, "--spec", "-s", help="Optional spec file to generate tests before running."),
    test_path: str = typer.Option("tests/generated", "--test-path", "-t", help="Path to tests to execute."),
    allure_dir: str = typer.Option("allure-results", "--allure-dir", "-a", help="Directory to store Allure results."),
    open_report: bool = typer.Option(False, "--open-report", "-o", help="Generate and open Allure HTML report after tests."),
    ssl_verify_cli: bool = typer.Option(None, "--ssl-verify/--no-ssl-verify", help="Enable or disable SSL verification."),
):
    """
    Optionally generate tests, then execute pytest and collect Allure reports.
    SSL verification can be set via CLI or environment variable QA_KIT_SSL_VERIFY.
    """
    # Determine SSL verification
    ssl_env = os.getenv("QA_KIT_SSL_VERIFY")
    if ssl_verify_cli is not None:
        ssl_verify = ssl_verify_cli
    elif ssl_env is not None:
        ssl_verify = ssl_env.lower() not in ("0", "false", "no")
    else:
        ssl_verify = False  # default

    exit_code = 1
    try:
        if spec:
            logger.info(f"📘 Generating tests from {spec} before run...")
            data = load_json(spec)
            TestGenerator(data, out_dir=test_path).generate()

        logger.info(f"🚀 Running pytest on {test_path} with Allure results in {allure_dir} (SSL_VERIFY={ssl_verify})")
        exit_code = run_pytest(
            test_path,
            extra_args=["--alluredir", allure_dir],
            allure_dir=allure_dir,
            open_report=open_report,
            ssl_verify=ssl_verify
        )

        if exit_code == 0:
            logger.info("✅ All tests passed successfully.")
        else:
            logger.warning(f"⚠️ Some tests failed (exit code {exit_code}).")

    except Exception as e:
        logger.exception("💥 Error while running tests.")
        exit_code = 1

    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    try:
        app()
    except typer.Exit as e:
        sys.exit(e.exit_code)
