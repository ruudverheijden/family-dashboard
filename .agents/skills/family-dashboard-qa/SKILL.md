---
name: family-dashboard-qa
description: Write and run executable pytest and Playwright tests for Family Dashboard requirements, regressions, and cross-browser failures.
---

Read the repository's AGENTS.md and the relevant parts of docs/REQUIREMENTS.md and docs/TESTING.md. Link coverage to requirement IDs or the reported behavior. Use the existing Python test stack and fixtures.

- Reproduce the reported sequence and starting state using synthetic data. For a bug fix, show the regression failing for the expected reason before the fix when reproducible. For a CI-only failure, inspect the failed job and its Playwright trace before changing the test.
- Choose unit tests for scheduling rules, API tests for persistence or conflicts, and Playwright for behavior that depends on browser interaction or layout. Reuse fixtures and run the smallest relevant set during iteration.
- For planning bugs, consider previously viewed future days, edited schedules, preserved history and points, week boundaries and Europe/Amsterdam time. Control the clock when a case depends on time. For UI failures, use the affected browser and viewport, including Linux fonts when reproducing GitHub failures.
- Use temporary databases, cache and synthetic integration responses. Report the exact test scope, failures or skips and any physical device or live integration checks still pending.
