# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/life-roles-skills-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, the only tests were the generic contract suite, and the API stored a role-project allocation whose `end_date` is before its `start_date`; a failed inline publish was logged but never reached Sentry.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — An allocation cannot end before it starts

- **Given** an owner with write permission
- **When** they create an allocation with `start_date` 2026-06-30 and `end_date` 2026-06-01
- **Then** the API answers 422 `invalid_value` naming both fields; the same day for both, or only one date, is accepted
- **Test:** `tests/test_allocation_validation.py::test_an_allocation_cannot_end_before_it_starts` · level: integration (API + throwaway PostgreSQL)

### AC-02 — Moving the end before the start is refused on update

- **Given** an allocation from 2026-06-01 to 2026-06-30
- **When** a patch sets `end_date` to 2026-05-31
- **Then** the API answers 422 and the stored `end_date` and version are unchanged; a patch that touches neither date still succeeds
- **Test:** `tests/test_allocation_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-03 — Share and priority stay in range

- **Given** a create request for an allocation
- **When** `allocation_percent` is outside 0..100 or `priority` outside 1..5
- **Then** the API answers 422; the boundary values are accepted
- **Test:** `tests/test_allocation_validation.py::test_allocation_percent_stays_between_0_and_100` · level: integration (API + throwaway PostgreSQL)

### AC-04 — A role cannot repeat a project and goal pair

- **Given** a role with an allocation for project 7 and goal 3
- **When** the same pair is allocated again, then with another goal
- **Then** the repeat is refused with 409; the other goal is accepted; without a goal the repeat is currently accepted
- **Test:** `tests/test_allocation_defaults.py::test_a_role_cannot_repeat_a_project_and_goal_pair` · level: integration (API + throwaway PostgreSQL)

### AC-05 — A role links to a target only once and must exist

- **Given** a role with a goal link
- **When** the same goal is linked again, or a link names a role that does not exist or belongs to another workspace
- **Then** the repeat is refused with 409 and the missing or foreign role with 422
- **Test:** `tests/test_role_defaults.py::test_a_role_links_to_each_target_only_once` · level: integration (API + throwaway PostgreSQL)

### AC-06 — Skills keep progress between 0 and 100 and refer to real categories

- **Given** a skill create or patch
- **When** `progress_percent` is 101 or `category_id` names a missing or foreign category
- **Then** the API answers 422 and the stored value is unchanged
- **Test:** `tests/test_skill_validation.py::test_progress_percent_is_checked_on_update_too` · level: integration (API + throwaway PostgreSQL)

### AC-07 — Records others depend on cannot be deleted

- **Given** a skill with a role-skill link and a role with a task link
- **When** the owner deletes the skill or the role
- **Then** the API answers 409 `has_dependents`; after the link is removed the delete succeeds
- **Test:** `tests/test_skill_queries.py::test_a_skill_in_use_cannot_be_deleted` · level: integration (API + throwaway PostgreSQL)

### AC-08 — A failed inline publish reaches Sentry

- **Given** a resource with graph events and a publisher token, and a publisher that raises
- **When** a record is created
- **Then** the request still succeeds (the cron sweep retries) and the error is passed to Sentry `capture()`; before the fix it was only logged
- **Test:** `tests/test_contract.py::test_inline_publish_failure_is_reported` · level: integration (API + throwaway PostgreSQL)

### AC-09 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `POST /v1/role-project-allocations`, `PATCH /v1/role-project-allocations/{id}` | changed | `end_date` before `start_date` -> `422 {"error": "invalid_value", "fields": ["end_date", "start_date"]}` |
| `cell.yaml` | changed | new resource key `ranges: [[start_date, end_date]]` on role-project-allocation |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "60"` (measured 62.76% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_allocation_validation.py::test_an_allocation_cannot_end_before_it_starts` | 1cf710f · `.venv/bin/pytest -q tests/test_allocation_validation.py::test_an_allocation_cannot_end_before_it_starts` · `assert 201 == 422` | CI run of the pushed tip | none |
| AC-02 | `tests/test_allocation_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` | 1cf710f · `.venv/bin/pytest -q tests/test_allocation_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · `assert 200 == 422` | CI run of the pushed tip | none |
| AC-03 | `tests/test_allocation_validation.py::test_allocation_percent_stays_between_0_and_100` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_allocation_defaults.py::test_a_role_cannot_repeat_a_project_and_goal_pair` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_role_defaults.py::test_a_role_links_to_each_target_only_once` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_skill_validation.py::test_progress_percent_is_checked_on_update_too` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_skill_queries.py::test_a_skill_in_use_cannot_be_deleted` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_contract.py::test_inline_publish_failure_is_reported` | 8391790 (origin/main) + this test only · `.venv/bin/pytest -q -k inline_publish tests/test_contract.py` · `assert captured` → `AssertionError` (nothing captured) | CI run of the pushed tip | none |
| AC-09 | `tests/test_contract.py::test_numbers_fit_their_columns` | c5317ae · `.venv/bin/pytest -q -k numbers_fit` · `psycopg.errors.NumericValueOutOfRange: integer out of range` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
