# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through the cell's own MCP server (`roles-skills-mcp`) and the hosted
  tool hub (`platform-mcp-remote-worker`, which lists this service's host in its allow-list).
- Local tooling that reads the cell through `EMPIRE_ROLES_SKILLS_API`: `ops-toolkit`
  (`cell_store.py`) and `mcp-aggregator` (`cell-store.ts`), as recorded in the online-systems
  registry.
- Other cells that point at goals, projects, contexts and tasks: those ids (`goal_id`,
  `project_id`, `context_id`, `task_id`) are plain numbers, not foreign keys. `role_id` is the
  text id of a role in the `ROLE-CATALOG` registry, not a row of this cell.
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `roles-skills.<resource>:read|write|delete` for each of the twelve resources.
- A web page that shows roles or skills: [ต้องยืนยัน].

## Product Purpose

What the owner is (personal roles), what they are learning (skills in categories, role learning
paths and a progress log) and where their time goes (role-to-goal, role-to-project and
role-to-task links, and role-project allocations with a share and a date range).

Success: each role and skill exists once, links point at the right roles and skills, and an
allocation never ends before it starts.

## Positioning

One capability, one service: its own API (Railway, serverless) with a publisher cron, its own
database (Neon) with row-level security per workspace, and authorization, executions and audit
through `empire-platform`. It is workspace-scoped, so the same service can serve other tenants
without code changes.

## Operating Context

- Production: `https://roles-skills-api-production.up.railway.app` (`/health`), deployed by
  merging to `main` after CI. The `roles-skills-publisher` cron (every 15 minutes) delivers graph
  events for roles, skills and progress entries.
- About 1,039 rows were imported from the retired SQLite tables keeping their ids (`legacy_id`).
- Monitored by `platform-uptime-worker` (target `roles-skills-api`); errors go to Sentry without
  personal data.

## Capabilities and Constraints

- Resources, each with list, stats, get, get-by-legacy-id, create (with `Idempotency-Key`), patch
  (with `expected_version`) and delete: `/v1/personal-roles`, `/v1/personal-role-context-links`,
  `/v1/personal-role-goal-links`, `/v1/personal-role-project-links`,
  `/v1/personal-role-task-links`, `/v1/role-goal-links`, `/v1/skill-categories` (listed by
  `sort_order`), `/v1/skills`, `/v1/role-path-steps`, `/v1/role-project-allocations`,
  `/v1/role-skill-links` and `/v1/progress-log`. Filters are the ones listed in the README; stats
  group by a filter only.
- Role rules: `slug` is unique (at most 200 characters); `slug`, `name` and `category` are
  required; `status` is planned, active, paused or retired. A role link points at one role that
  exists in the same workspace, once per target (409 on repeat); the same target may link to
  several roles.
- Skill rules: category `name` and `slug` are unique, a category may have a `parent_id`; skill
  `slug` is unique; `level` and `target_level` are L1_deep, L2_capable, L3_overview or
  L4_outsource; `progress_percent` is 0 to 100; `category_id` must exist in the same workspace.
- Role-skill link, path step and progress rules: a role links to a skill once; a step key is
  unique per role and registry; `phase_id` is orient, learn, practice, evidence or operate;
  `target_progress`, `progress_before` and `progress_after` are 0 to 100; `hours_spent` is not
  negative; `evidence_url` is at most 2000 characters.
- Allocation rules: `allocation_percent` is 0 to 100 and `priority` 1 to 5; a role has one
  allocation per project and goal; `end_date` cannot be before `start_date` (422
  `invalid_value` naming both fields, on create and on patch; the same day is allowed).
  Allocations with no `goal_id` are not deduplicated, so a role can repeat a project while no goal
  is set.
- A role, skill or category that other records point at cannot be deleted until they are removed
  (409 `has_dependents`). Unknown fields are refused (422); an unchanged patch keeps the version.
- Out of scope: checking that goals, projects, contexts and tasks exist in their own services,
  checking that allocations of one role add up to 100, and the content of the role catalog.

## Measures

Proposed, nothing collects them yet:

- Active roles with at least one goal, project or task link.
- Skills with a progress entry in the last 30 days.
- Active allocations whose `end_date` has passed (target: 0).
- 5xx rate and p95 latency on `/v1/skills` (Sentry and uptime worker).
