import logging
from pathlib import Path
import typer
import sys
import os

from qa_kit.utils import load_json
from qa_kit.generator import TestGenerator
from qa_kit.runner import run_pytest

app = typer.Typer(
    help="QA-Kit: Generate and run API integration tests from JSON specs."
)

# ---------------- Logging Setup ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------- Generate Command ---------------- #
@app.command()
def generate(
    spec: str = typer.Argument(
        ..., help="Path to a JSON spec file or directory containing multiple specs."
    ),
    out: str = typer.Option(
        "tests/generated",
        "--out",
        "-o",
        help="Output directory for generated pytest files.",
    ),
    delta: bool = typer.Option(
        False,
        "--delta/--no-delta",
        help="Only regenerate new or changed tests (skip unchanged).",
    ),
    clean: bool = typer.Option(
        False,
        "--clean/--no-clean",
        help="Remove test files that no longer exist in the JSON spec(s).",
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose/--no-verbose",
        "-v",
        help="Show detailed per-file generation messages.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Do not write files, only show what would be generated.",
    ),
):
    """
    Generate pytest test files from one or more JSON spec definitions.
    Supports single-file or directory-based generation.
    """
    try:
        spec_path = Path(spec)
        if not spec_path.exists():
            typer.secho(f"❌ Spec path not found: {spec_path}", fg=typer.colors.RED)
            raise typer.Exit(code=2)

        # Collect JSON files
        if spec_path.is_dir():
            json_files = sorted(list(spec_path.rglob("*.json")))
            if not json_files:
                typer.secho(
                    "⚙️ No specification files found in directory.",
                    fg=typer.colors.BRIGHT_BLACK,
                )
                raise typer.Exit(code=0)
        elif spec_path.is_file() and spec_path.suffix == ".json":
            json_files = [spec_path]
        else:
            typer.secho(
                "⚙️ No valid JSON specification file found.",
                fg=typer.colors.BRIGHT_BLACK,
            )
            raise typer.Exit(code=0)

        total_generated = 0

        if dry_run:
            typer.secho(
                "👀 Dry-run mode enabled (no files will be written)",
                fg=typer.colors.YELLOW,
            )

        for json_file in json_files:
            typer.secho(f"📄 Loading spec: {json_file}", fg=typer.colors.CYAN)
            data = load_json(str(json_file))

            generator = TestGenerator(spec_data=data, out_dir=out, verbose=verbose)
            files = generator.generate(
                delta=delta, clean_removed=clean, dry_run=dry_run
            )
            total_generated += len(files)

        if total_generated == 0:
            typer.secho(
                "⚙️ Nothing found to generate — all tests are up to date!",
                fg=typer.colors.BRIGHT_BLACK,
            )
        else:
            typer.secho(
                f"✅ Generated or updated {total_generated} test file(s) in '{out}'",
                fg=typer.colors.GREEN,
            )
            if delta:
                typer.secho(
                    "🔁 Delta mode enabled — only new or modified tests processed.",
                    fg=typer.colors.YELLOW,
                )
            if clean:
                typer.secho(
                    "🧹 Cleanup mode enabled — removed obsolete tests.",
                    fg=typer.colors.CYAN,
                )

    except Exception as e:
        logger.exception("💥 Error generating test files")
        typer.secho(f"💥 Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from e


# ---------------- Run Command ---------------- #
@app.command()
def run(
    spec: str = typer.Option(
        None,
        "--spec",
        "-s",
        help="Optional spec file or directory to generate tests before running.",
    ),
    test_path: str = typer.Option(
        "tests/generated",
        "--test-path",
        "-t",
        help="Path to tests to execute.",
    ),
    allure_dir: str = typer.Option(
        "allure-results",
        "--allure-dir",
        "-a",
        help="Directory to store Allure results.",
    ),
    open_report: bool = typer.Option(
        False,
        "--open-report",
        "-o",
        help="Generate and open Allure HTML report after tests.",
    ),
    ssl_verify_cli: bool = typer.Option(
        None,
        "--ssl-verify/--no-ssl-verify",
        help="Enable or disable SSL verification (overrides env).",
    ),
):
    """
    Optionally generate tests, then execute pytest and collect Allure reports.
    SSL verification can be set via CLI or environment variable QA_KIT_SSL_VERIFY.
    """
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
            typer.secho(
                f"📘 Generating tests from {spec} before run...", fg=typer.colors.CYAN
            )
            spec_path = Path(spec)

            if spec_path.is_dir():
                json_files = sorted(list(spec_path.rglob("*.json")))
                if not json_files:
                    typer.secho(
                        "⚙️ No specification files found in directory.",
                        fg=typer.colors.BRIGHT_BLACK,
                    )
                    raise typer.Exit(code=0)
            else:
                json_files = [spec_path]

            for json_file in json_files:
                data = load_json(str(json_file))
                TestGenerator(data, out_dir=test_path).generate()

        typer.secho(
            f"🚀 Running pytest on {test_path} with Allure results in {allure_dir} (SSL_VERIFY={ssl_verify})",
            fg=typer.colors.GREEN,
        )
        exit_code = run_pytest(
            test_path,
            extra_args=["--alluredir", allure_dir],
            allure_dir=allure_dir,
            open_report=open_report,
            ssl_verify=ssl_verify,
        )

        if exit_code == 0:
            typer.secho("✅ All tests passed successfully.", fg=typer.colors.GREEN)
        else:
            typer.secho(
                f"⚠️ Some tests failed (exit code {exit_code}).", fg=typer.colors.YELLOW
            )

    except Exception as e:
        logger.exception("💥 Error while running tests.")
        typer.secho(f"💥 Error: {e}", fg=typer.colors.RED)
        exit_code = 1

    raise typer.Exit(code=exit_code)


# ---------------- Entry Point ---------------- #
if __name__ == "__main__":
    try:
        app()
    except typer.Exit as e:
        sys.exit(e.exit_code)
