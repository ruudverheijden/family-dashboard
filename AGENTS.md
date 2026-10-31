# Project guidelines

## Definition of done

- Understand the existing behavior and nearby tests before changing code.
- Add or update a regression test for bug fixes. Test new behavior at the lowest useful level: unit tests for isolated logic, API tests for backend behavior, and Playwright for important user-facing flows.
- Update `docs/REQUIREMENTS.md` when product requirements or their status change. Update user or operator documentation when behavior, configuration, installation, or recovery steps change.
- Record verification in `docs/VERIFICATION.md` only after performing it. Clearly distinguish automated results from manual checks and unverified items.
- Run the relevant tests and checks below. In the handoff or pull request, state what changed, what was tested, and any remaining gaps.

## Checks

- Backend: `.venv/bin/python -m pytest -q`
- Browser acceptance: follow `docs/TESTING.md`
- Python lint: `.venv/bin/ruff check .`
- Python formatting: `.venv/bin/ruff format --check .`
- CSS formatting: `.venv/bin/python tools/format_css.py --check`
- JavaScript formatting: `npm ci --ignore-scripts` once, then `npm run format:check`
- JavaScript syntax and module boundaries: `node --check app/static/app.js` and `node --experimental-vm-modules tools/check_frontend.mjs`

CI runs the backend tests, Ruff, JavaScript syntax check, container build, and health check. Do not treat a configured CI job or a fixture-based integration test as evidence of a check that has not actually run.

## Project conventions

- Follow the existing Python, HTML, CSS, and JavaScript patterns; Ruff configuration is in `pyproject.toml`.
- Keep tests isolated from real `.env` values, databases, caches, and integration credentials. Use temporary data and fictitious credentials.
- See `docs/TESTING.md`, `docs/REQUIREMENTS.md`, and `docs/VERIFICATION.md` for detailed test scope, product requirements, and recorded evidence.

## Architecture and safe changes

Read `docs/ARCHITECTURE.md` for module responsibilities and the behavioral contracts.
- `app/main.py` only exposes the application. Configure test instances through `create_app(AppConfig(...))`; never point tests at real data or load `.env`.
- HTTP/authentication belongs in `routes.py`/`auth.py`; business actions in `services/`; normalization in `validation.py`; storage in `db.py`.
- Preserve one transaction for execution completion, points, history and request deduplication. Do not open a second connection inside a ledger helper.
- CalDAV and Immich own separate synchronization state. Never hold a database transaction or photo lock during upstream network I/O. When both are needed, acquire the photo lock before the database transaction.
- Settings changes invalidate pending photo responses. Check configuration versions before publishing upstream results. Log error categories, never credentials or raw upstream exceptions.
- Browser code uses native modules under `app/static/js/`. Shared UI state is explicit in `state.js`; cross-feature coordination is wired in `app.js` through `actions.js`. Keep imports acyclic and feature-private state private.
- Preserve CSS rule order during formatting. Consolidating the cascade is a separate, visually verified task.
- Before editing, inspect current uncommitted changes; preserve concurrent user changes. Use small changes and rerun affected checks against the combined working tree.
