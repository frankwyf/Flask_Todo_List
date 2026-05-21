# Flask Task Tracker (Open-Source Portfolio Edition)

A Flask-based task management web app refactored from an academic prototype into a portfolio-ready open-source project.

## Highlights
- User registration and login
- Task CRUD, completion toggling, and editing
- Search/filter by status, module, and task name
- Upcoming deadline filter (`/searchUpcoming`)
- CSV export and simple tasks API endpoint (`/exportTasks`, `/api/tasks`)
- Task summary API and health endpoint (`/api/summary`, `/healthz`)
- Basic analytics charts (ECharts)
- Production-style Blueprint routing (`auth`, `task`, `chart`)
- Click-flow test suite in isolated test directory
- Portfolio API docs page and architecture diagram page
- GitHub Actions test pipeline
- Optional email reminder integration
- Optional weather widget integration

## Security and Desensitization
This release removes hardcoded secrets and private information.

- Credentials are no longer stored in source code
- SMTP sender/password are environment-driven
- Weather API key is environment-driven
- Personal identifiers in templates were removed
- `.gitignore` and `.env.example` added for safe open-source publishing

## Open-Source Governance Files
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`
- `CHANGELOG.md`
- `.github/ISSUE_TEMPLATE/*`
- `.github/pull_request_template.md`
- `.github/dependabot.yml`
- `.editorconfig` and `.gitattributes`

## Quick Start (Windows PowerShell)
1. Create a virtual environment:

```powershell
py -3 -m venv .venv
```

2. Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Copy example env and edit values if needed:

```powershell
Copy-Item .env.example .env
```

5. Initialize tables:

```powershell
python db_create.py
```

6. Run the app:

```powershell
python run.py
```

Open `http://127.0.0.1:5000/` in your browser.

## Configuration
Use environment variables (see `.env.example`):

- `SECRET_KEY`
- `DATABASE_URL` (default: SQLite `instance/app.db`)
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_SSL`, `MAIL_USE_TLS`
- `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
- `WEATHER_WIDGET_KEY`

If mail settings are not configured, reminder email sending is not available.

## Project Structure
```text
.
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- model.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- task.py
|   |   `-- chart.py
|   |-- templates/
|   |   |-- portfolio_api.html
|   |   `-- portfolio_architecture.html
|   `-- static/
|-- .github/
|   `-- workflows/
|       `-- tests.yml
|-- docs/
|   |-- README.en.md
|   |-- README.zh-CN.md
|   `-- README.ja.md
|-- tests/
|   |-- click/
|   |   |-- conftest.py
|   |   `-- test_click_flow.py
|   |-- runtime/
|   `-- requirements.txt
|-- db_create.py
|-- run.py
|-- pytest.ini
|-- requirements.txt
|-- .env.example
`-- LICENSE
```

## Run Click-Level Tests
1. Install test dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
```

2. Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Portfolio Pages
- API guide: `http://127.0.0.1:5000/portfolio/api`
- Architecture diagram: `http://127.0.0.1:5000/portfolio/architecture`

## UI Upgrade Notes
- Added a portfolio visual layer (`app/static/css/portfolio-upgrade.css`)
- Added dashboard KPI cards and progress bar on home page
- Added quick links for docs, API, export, and upcoming tasks
- Added light/dark theme toggle with preference persistence

## CI
GitHub Actions workflow file: `.github/workflows/tests.yml`
It runs click-flow tests on pushes and pull requests.

## Multilingual Documentation
- English detailed guide: [docs/README.en.md](docs/README.en.md)
- 中文详细文档: [docs/README.zh-CN.md](docs/README.zh-CN.md)
- 日本語詳細ドキュメント: [docs/README.ja.md](docs/README.ja.md)

## Roadmap
- Improve form validation and CSRF handling
- Add Docker pipeline

## License
MIT License. See [LICENSE](LICENSE).