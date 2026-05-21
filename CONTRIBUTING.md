# Contributing Guide

Thanks for your interest in contributing.

## Development Setup
1. Create venv:
   - `py -3 -m venv .venv`
2. Activate:
   - `./.venv/Scripts/Activate.ps1`
3. Install deps:
   - `pip install -r requirements.txt`
   - `pip install -r tests/requirements.txt`
4. Run app:
   - `python db_create.py`
   - `python run.py`
5. Run tests:
   - `pytest`

## Branch and Commit
- Create feature branches from `main`.
- Use clear commit messages, for example:
  - `feat: add csv export`
  - `fix: handle invalid datetime parsing`

## Pull Request Checklist
- [ ] Code builds and app runs locally
- [ ] Tests pass (`pytest`)
- [ ] No secrets or personal data added
- [ ] README/docs updated if behavior changed
- [ ] UI changes include screenshots when possible

## Style Notes
- Keep changes focused and minimal.
- Preserve existing route behavior unless intentionally changed.
- Prefer adding docs/tests together with features.
