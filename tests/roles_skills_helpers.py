"""Shared helpers for the roles-and-skills domain tests."""

import uuid
from typing import Any

PERSONAL_ROLES = "/v1/personal-roles"
CONTEXT_LINKS = "/v1/personal-role-context-links"
GOAL_LINKS = "/v1/personal-role-goal-links"
PROJECT_LINKS = "/v1/personal-role-project-links"
TASK_LINKS = "/v1/personal-role-task-links"
ROLE_GOAL_LINKS = "/v1/role-goal-links"
SKILL_CATEGORIES = "/v1/skill-categories"
SKILLS = "/v1/skills"
ROLE_PATH_STEPS = "/v1/role-path-steps"
ALLOCATIONS = "/v1/role-project-allocations"
ROLE_SKILL_LINKS = "/v1/role-skill-links"
PROGRESS_LOG = "/v1/progress-log"


def unique(prefix: str = "x") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def other_workspace(harness: Any, platform: Any) -> dict[str, str]:
    """A token of another workspace whose actor may do everything there."""
    actor = uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    return harness.token(actor, uuid.uuid4())


def make(
    client: Any, headers: dict[str, str], path: str, **body: Any
) -> dict[str, Any]:
    response = client.post(path, headers=headers, json=body)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_role(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"slug": unique("role"), "name": "Engineer", "category": "work", **fields}
    return client.post(PERSONAL_ROLES, headers=owner, json=body)


def new_role(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    return make(
        client,
        owner,
        PERSONAL_ROLES,
        **{"slug": unique("role"), "name": "Engineer", "category": "work", **fields},
    )


def create_category(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"name": unique("cat"), "slug": unique("cat"), **fields}
    return client.post(SKILL_CATEGORIES, headers=owner, json=body)


def new_category(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    response = create_category(client, owner, **fields)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_skill(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"name": "Python", "slug": unique("skill"), **fields}
    return client.post(SKILLS, headers=owner, json=body)


def new_skill(client: Any, owner: dict[str, str], **fields: Any) -> dict[str, Any]:
    response = create_skill(client, owner, **fields)
    assert response.status_code == 201, response.text
    created: dict[str, Any] = response.json()
    return created


def create_allocation(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"role_id": unique("ROLE"), "project_id": 1, **fields}
    return client.post(ALLOCATIONS, headers=owner, json=body)


def create_step(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "role_id": unique("ROLE"),
        "step_key": unique("step"),
        "phase_id": "learn",
        "title": "Read the guide",
        "action": "Read it",
        "completion_rule": "Notes written",
        **fields,
    }
    return client.post(ROLE_PATH_STEPS, headers=owner, json=body)


def create_skill_link(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {"role_id": unique("ROLE"), "learning_path": "docs/path.md", **fields}
    return client.post(ROLE_SKILL_LINKS, headers=owner, json=body)


def create_progress(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    return client.post(
        PROGRESS_LOG, headers=owner, json={"title": "Practised", **fields}
    )
