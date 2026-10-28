# life-roles-skills-api
The Roles and skills cell: its own API (Railway, serverless) and its own Neon
database, described by `cell.yaml` and served by the code in `src/cellkit/`, which
this repository owns. It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `life-roles-skills-api`, service `roles-skills-api` (Serverless) |
| Publisher | service `roles-skills-publisher` (Railway cron, `5 * * * *`) |
| Data | Neon project `life-roles-skills-api`, database `roles_skills` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`roles-skills`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `roles-skills.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/personal-roles` | personal-role | `category`, `status` |
| `/v1/personal-role-context-links` | personal-role-context-link | `personal_role_id`, `context_id`, `relation_type` |
| `/v1/personal-role-goal-links` | personal-role-goal-link | `personal_role_id`, `goal_id`, `link_type` |
| `/v1/personal-role-project-links` | personal-role-project-link | `personal_role_id`, `project_id`, `link_type` |
| `/v1/personal-role-task-links` | personal-role-task-link | `personal_role_id`, `task_id`, `link_type` |
| `/v1/role-goal-links` | role-goal-link | `role_id`, `goal_id`, `link_type` |
| `/v1/skill-categories` | skill-category | `parent_id` |
| `/v1/skills` | skill | `category_id`, `level`, `target_level`, `status`, `priority`, `revenue_relevant` |
| `/v1/role-path-steps` | role-path-step | `role_id`, `phase_id`, `skill_id`, `source_registry` |
| `/v1/role-project-allocations` | role-project-allocation | `role_id`, `project_id`, `goal_id`, `status` |
| `/v1/role-skill-links` | role-skill-link | `role_id`, `skill_id`, `link_type` |
| `/v1/progress-log` | progress-entry | `skill_id`, `activity_type` |

## Develop and operate

```bash
uv sync --frozen --all-extras          # Python 3.12 (.python-version): pgserver has no cp313 wheel yet
.venv/bin/pytest -q
.venv/bin/mypy . && uvx ruff@0.17.1 check . && uvx ruff@0.17.1 format --check .   # the same checks CI runs
NEON_API_KEY=... .venv/bin/roles-skills-db provision
npm install && railway config apply   # service settings only; code deploys from GitHub (below)
```

Dependencies are locked in `uv.lock`; the image installs them with `uv sync --frozen`, so
production runs the versions CI tested. Change a dependency with `uv add`/`uv lock` and commit
the lock. Product scope and measures: [PRODUCT.md](PRODUCT.md); change records: `specs/`.

Deploys (CD, since 2026-10-18): `roles-skills-api` and `roles-skills-publisher` are connected
to this repository's `main` with Railway's Wait for CI (`checkSuites`). A merge to `main`
deploys only after the CI and security checks pass; a failing check leaves production on the
previous deployment. Roll back by redeploying an earlier deployment in Railway. `railway up` is
no longer used.

Railway variables: `SENTRY_DSN` (error reporting; unset = off, see
`src/cellkit/_sentry.py`), `ROLES_SKILLS_DB_MODE=hosted`, `ROLES_SKILLS_DB_URL_API`,
`ROLES_SKILLS_JWT_PUBLIC_KEY_PEM`, `ROLES_SKILLS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`, and for the publisher `ROLES_SKILLS_DB_URL_PUBLISHER` and `ROLES_SKILLS_PUBLISHER_TOKEN`.
