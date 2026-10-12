# roles-skills

The Roles and skills cell: its own API (Railway, serverless) and its own Neon
database, described by `cell.yaml` and served by the code in `src/cellkit/`, which
this repository owns. It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `solo-roles-skills`, service `roles-skills-api` (Serverless) |
| Publisher | service `roles-skills-publisher` (Railway cron, `*/15 * * * *`) |
| Data | Neon project `solo-roles-skills`, database `roles_skills` |
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
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/roles-skills-db provision
npm install && railway config apply && railway up --ci --service roles-skills-api
```

Railway variables: `ROLES_SKILLS_DB_MODE=hosted`, `ROLES_SKILLS_DB_URL_API`,
`ROLES_SKILLS_JWT_PUBLIC_KEY_PEM`, `ROLES_SKILLS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`, and for the publisher `ROLES_SKILLS_DB_URL_PUBLISHER` and `ROLES_SKILLS_PUBLISHER_TOKEN`.
