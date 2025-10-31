# qa-kit
Work in progress
qa-kit — Production-ready Test Generator
Generates pytest integration tests from a JSON test specification file (API URL, method, params,
body, expected response)
Provides a CLI to generate and run tests ( Typer )
Uses Poetry for packaging
Includes httpx, pytest-asyncio and allure-pytest integration
Adds robust error handling, logging, and pytest fixtures
Ships a GitHub Actions workflow to run tests and publish Allure reports
You can copy these files into a repo qa-kit install and you're ready to generate and run tests.

## Installation

```bash
pip install qa-kit
```
## Usage    
```bash
from qa_kit import hello
print(hello())
```

---

## 6️⃣ LICENSE

Use MIT or your preferred license.

---

## 7️⃣ Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - minimal PyPI-ready package"
git branch -M main
git remote add origin git@github.com:your-personal-username/qa-kit.git
git push -u origin main
```