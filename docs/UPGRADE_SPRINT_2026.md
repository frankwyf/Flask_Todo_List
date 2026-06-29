# Upgrade Sprint 2026

## Goal
Perform a full-stack, portfolio-grade modernization sprint with phased validation and incremental commits.

## Research Inputs
- Flask official docs: configuration and testing best practices
- GitHub Actions official docs: matrix testing, pip cache, artifacts
- pip-audit project docs: dependency vulnerability scanning

## Execution Plan
1. Backend hardening and analytics APIs
2. UI visualization and interaction enhancement
3. Test expansion and engineering quality gate
4. CI/CD workflow upgrade and release artifact automation

## Delivered Upgrades
- Added environment-aware config classes (development/testing/production)
- Added HTTP security headers baseline in app responses
- Added `GET /api/insights` for KPI + distribution analytics
- Added `GET /api/timeline` for deadline timeline aggregation
- Upgraded `GET /api/summary` with overdue/upcoming metrics
- Added robust user_id validation and safer route behavior
- Added user-scoped overdue query fix
- Added dynamic dashboard intelligence board (live metrics + charts)
- Refactored dashboard JS for stronger validation and reusable rendering logic
- Added dev tooling config: Ruff + pip-audit + pytest-cov
- Added local one-shot QA script: `scripts/quality-gate.ps1`
- Expanded CI workflow to lint + matrix tests + coverage + security report
- Added release workflow for tag-based source archive packaging

## Validation Strategy
- Baseline tests before modifications
- Re-run all tests after each batch
- Keep commits scoped by layer (backend, UI, CI)

## Outcome
- Test suite remains green after upgrades
- CI pipeline now covers code quality, compatibility, and security
- Project demonstrates stronger Python web engineering depth for portfolio review
