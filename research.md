# Universal Protocol Suite Research (Portable, 2025)

Date: 2025-10-04
Scope: Select the most portable, fast, and secure tooling for Python-based projects (with a FastAPI/CLI/Docker footprint) and GitHub Actions CI/CD. Consolidate current best practices to drive Phase 1–5 integration.

---

## TL;DR Recommendations (portable defaults)

- Package manager: Prefer uv (Astral) for speed and portability; keep pip fallbacks.
- Testing: pytest (+ pytest-asyncio, coverage.py); Playwright/Cypress optional for E2E.
- Sentry Layer (pre-commit): pre-commit with ruff (lint+imports), black (format), gitleaks (secrets). Keep configs cross-platform.
- CI/CD (GitHub Actions): checkout@v4, setup-python@v5 (note v6 exists with breaking changes), cache@v4; ubuntu-latest (24.04). Jobs: lint, test+coverage, build, security scan (CodeQL, Trivy fs, dependency-review, pip-audit or OSV-Scanner). Use concurrency cancel-in-progress.
- Docker/Containers: Compose v2; avoid version: key; bind services to 127.0.0.1 for local-only; minimal privileges; healthchecks; deterministic networking.
- App (FastAPI GUI): SSE is adequate for 1-way streaming; rate-limiting via fastapi-limiter/SlowAPI; add security headers middleware.

---

## Package Management (Python)

- uv (Astral) — extremely fast Python package and project manager written in Rust; supports pip-compatible workflows, pyproject/PEP standards.
  - Docs: https://docs.astral.sh/uv/getting-started/installation/
  - GitHub: https://github.com/astral-sh/uv
  - Astral company page (Ruff, uv): https://astral.sh/
  - Compatibility notes: https://docs.astral.sh/uv/pip/compatibility/
  - Using uv in GitHub Actions: https://docs.astral.sh/uv/guides/integration/github/
- Comparative context (2024–2025): discussions and articles reflect rapid uv adoption and performance upside vs pip/poetry.
  - Poetry vs uv analysis (2024): https://www.loopwerk.io/articles/2024/python-poetry-vs-uv/
  - Datacamp guide (2025): https://www.datacamp.com/tutorial/python-uv
- PEP/packaging ecosystem changes 2025 (indicative): pylock.toml (PEP 751) adoption discussions; uv compatibility with pip mechanisms.
  - Thread: https://discuss.python.org/t/community-adoption-of-pylock-toml-pep-751/89778

Practical recommendation:
- Prefer uv for local dev and CI for speed and reproducibility. Provide pip fallbacks in docs.
- Default commands:
  - uv: uv venv; uv pip install -r requirements.txt or uv add pkg; uv run pytest
  - pip fallback: python -m venv .venv && .venv activation; pip install -r requirements.txt

---

## Testing Stack (unit/integration)

- pytest (current, stable):
  - Changelog: https://docs.pytest.org/en/stable/changelog.html
  - Releases: https://github.com/pytest-dev/pytest/releases
- pytest-asyncio for async tests
  - PyPI: https://pypi.org/project/pytest-asyncio/
  - Docs/Changelog: https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html
- coverage.py for coverage reports
  - Docs: https://coverage.readthedocs.io/
  - PyPI: https://pypi.org/project/coverage/

Practical recommendation:
- Use pytest with pytest-asyncio and coverage; export XML for CI reporting.

---

## Sentry Layer (pre-commit guardrails)

- pre-commit framework:
  - Site: https://pre-commit.com/
  - Hooks catalog: https://pre-commit.com/hooks.html
- Lint/format tools:
  - ruff (fast linter; can also sort imports): https://github.com/astral-sh/ruff, release blog 2025: https://astral.sh/blog/ruff-v0.9.0
  - black (formatter): https://pypi.org/project/black/
- Secrets scanning:
  - gitleaks action: https://github.com/gitleaks/gitleaks-action
  - gitleaks core: https://github.com/gitleaks/gitleaks

Practical recommendation:
- pre-commit with hooks: ruff (lint, fix), black (format), ruff (isort rules) or isort if preferred, gitleaks (pre-commit via local hook or CI job). Keep configs minimal and portable.

---

## Security & Vulnerability Scanning

- GitHub Dependency Review Action:
  - https://github.com/actions/dependency-review-action
  - Docs: https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review
- CodeQL (GitHub Advanced Security):
  - CodeQL action: https://github.com/github/codeql-action
  - Supported languages: https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/
  - Changelog examples: https://codeql.github.com/docs/codeql-overview/codeql-changelog/codeql-cli-2.19.0/
- Trivy (Aqua Security) for filesystem scan (SCA, misconfig, secrets):
  - Action: https://github.com/aquasecurity/trivy-action
  - Project: https://github.com/aquasecurity/trivy
- Python-specific SCA:
  - pip-audit action: https://github.com/pypa/gh-action-pip-audit
  - OSV-Scanner action: https://github.com/google/osv-scanner-action (multi-ecosystem)
- Secret scanning (GitHub push protection):
  - About push protection: https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection
  - 2025 updates: https://github.blog/changelog/2025-08-19-secret-scanning-configuring-patterns-in-push-protection-is-now-generally-available/

Practical recommendation:
- In PRs: dependency-review-action
- Nightly/weekly: trivy fs . and pip-audit or OSV-Scanner
- Enable secret scanning push protection in repo settings (org policy if available)

---

## CI/CD (GitHub Actions 2025)

- Runners & images:
  - ubuntu-latest targets Ubuntu 24.04 (since 2024–2025): https://github.com/actions/runner-images/issues/10636
  - Runner images repo: https://github.com/actions/runner-images
- Core actions:
  - checkout@v4: https://github.com/actions/checkout
  - setup-python@v5 (v6 exists with breaking changes note): https://github.com/actions/setup-python
  - cache@v4 (Cache API v2 required from 2025-04-15): https://github.com/actions/cache, cache docs: https://docs.docker.com/build/ci/github-actions/cache/
- Using uv in Actions:
  - Guide: https://docs.astral.sh/uv/guides/integration/github/
  - setup-uv: https://github.com/astral-sh/setup-uv
- Concurrency controls:
  - Docs: https://docs.github.com/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs

Practical recommendation:
- Workflow matrix: {python: [3.10, 3.11, 3.12, 3.13]}
- Jobs: build-and-verify (lint, test, coverage, build); security-scan (CodeQL init/analyze + trivy fs + pip-audit/OSV); scaffold E2E job commented.
- Enable concurrency cancel-in-progress for PR workflows.

---

## Containers & Docker Compose (v2)

- Compose v2 docs: https://docs.docker.com/compose/
- Remove deprecated version: key (Compose v2 ignores it): forum note: https://forums.docker.com/t/docker-compose-yml-version-is-obsolete/141313
- Local binding security:
  - Map to 127.0.0.1:HOST:CONTAINER for local-only: discussion/examples:
    - https://www.jeffgeerling.com/blog/2020/be-careful-docker-might-be-exposing-ports-world
    - https://www.reddit.com/r/selfhosted/comments/1cv2l3q/security_psa_for_anyone_using_docker_on_a/
- Trivy scans in CI for container FS (if building images): https://github.com/aquasecurity/trivy-action

Practical recommendation:
- Use 127.0.0.1 bindings for dev; add healthchecks; prefer non-root images when possible; minimal capabilities; Compose profiles for optional services.

---

## FastAPI: Streaming, Security, Rate limiting

- SSE
  - Production SSE lib for Starlette/FastAPI: https://github.com/sysid/sse-starlette
  - FastAPI custom responses: https://fastapi.tiangolo.com/advanced/custom-response/
  - SSE vs WebSockets (context): https://softwaremill.com/sse-vs-websockets-comparing-real-time-communication-protocols/
- Rate limiting
  - Guides and libs (2025): SlowAPI / fastapi-limiter patterns: example guide: https://medium.com/@rameshkannanyt0078/rate-limiting-throttling-in-fastapi-a-complete-guide-5ef746cd26b5
- Security headers & middleware
  - Examples of custom middleware adding security headers in FastAPI/Starlette: https://blog.stackademic.com/taking-fastapi-to-the-next-level-writing-custom-middleware-for-logging-monitoring-and-enhanced-e960cdeea281

Practical recommendation:
- Keep SSE for 1-way streaming; consider sse-starlette for robustness.
- Add basic rate limiting middleware for Enhance endpoint; keep server bind local-only in dev.
- Add security headers middleware (CSP where applicable), and CORS disabled or restricted.

---

## E2E test options (optional)

- Playwright (official CI docs): https://playwright.dev/docs/ci-intro
- Cypress (official GH Action): https://github.com/cypress-io/github-action, docs: https://docs.cypress.io/app/continuous-integration/github-actions

Practical recommendation:
- Scaffold E2E job commented in workflow; enable later once a staging or headful environment is decided.

---

## Governance & Documentation

- Use Diátaxis structure for docs: tutorials, how-to, explanation, reference (general approach, not a single canonical link).
- CONTRIBUTING.md should describe:
  - How to install dev tools (uv/pip)
  - How to run linters/formatters/tests locally
  - pre-commit install instructions and common troubleshooting
- BUSINESS_CASE.md: capture value, scope, ownership, success metrics.

---

## Portability Considerations (Win/macOS/Linux)

- Prefer shell-agnostic instructions; when OS-specific, provide separate snippets (PowerShell vs Bash).
- Avoid hard dependencies on Docker Desktop features; use Compose v2 syntax.
- Keep network exposure local (127.0.0.1) by default; document overrides.
- Use uv or pip commands that work on all OSes; avoid path-specific assumptions.

---

## Sources (selected)
- uv: https://docs.astral.sh/uv/getting-started/installation/ | https://docs.astral.sh/uv/guides/integration/github/ | https://docs.astral.sh/uv/pip/compatibility/ | https://github.com/astral-sh/uv | https://astral.sh/
- pre-commit: https://pre-commit.com/ | https://pre-commit.com/hooks.html
- ruff: https://github.com/astral-sh/ruff | https://astral.sh/blog/ruff-v0.9.0
- black: https://pypi.org/project/black/
- pytest: https://docs.pytest.org/en/stable/changelog.html | https://github.com/pytest-dev/pytest/releases
- pytest-asyncio: https://pypi.org/project/pytest-asyncio/ | https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html
- coverage.py: https://coverage.readthedocs.io/
- GitHub Actions: https://github.com/actions/checkout | https://github.com/actions/setup-python | https://github.com/actions/cache | https://docs.github.com/actions | https://github.com/actions/runner-images
- Dependency review: https://github.com/actions/dependency-review-action | https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review
- CodeQL: https://github.com/github/codeql-action | https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/
- Trivy: https://github.com/aquasecurity/trivy-action | https://github.com/aquasecurity/trivy
- pip-audit: https://github.com/pypa/gh-action-pip-audit | OSV-Scanner: https://github.com/google/osv-scanner-action
- Secret scanning push protection: https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection
- Docker Compose v2: https://docs.docker.com/compose/ | Port binding cautions: https://www.jeffgeerling.com/blog/2020/be-careful-docker-might-be-exposing-ports-world
- FastAPI SSE: https://github.com/sysid/sse-starlette | https://fastapi.tiangolo.com/advanced/custom-response/

