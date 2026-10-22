"""What personal roles, their links and role-goal links refuse."""

from roles_skills_helpers import (
    CONTEXT_LINKS,
    GOAL_LINKS,
    PERSONAL_ROLES,
    PROJECT_LINKS,
    ROLE_GOAL_LINKS,
    TASK_LINKS,
    create_role,
    new_role,
    other_workspace,
    unique,
)

LINK_PATHS = {
    "context": (CONTEXT_LINKS, "context_id"),
    "goal": (GOAL_LINKS, "goal_id"),
    "project": (PROJECT_LINKS, "project_id"),
    "task": (TASK_LINKS, "task_id"),
}


def test_a_role_needs_a_slug_name_and_category(client, owner):
    complete = {"slug": unique("role"), "name": "Engineer", "category": "work"}
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        assert (
            client.post(PERSONAL_ROLES, headers=owner, json=body).status_code == 422
        ), missing


def test_role_text_limits(client, owner):
    assert create_role(client, owner, slug="s" * 201).status_code == 422
    assert create_role(client, owner, name="n" * 501).status_code == 422
    assert create_role(client, owner, category="c" * 201).status_code == 422
    assert create_role(client, owner, source="x" * 201).status_code == 422
    assert create_role(client, owner, slug="s" * 200, name="n" * 500).status_code == 201


def test_role_status_must_be_a_known_state(client, owner):
    assert create_role(client, owner, status="archived").status_code == 422
    assert create_role(client, owner, status="retired").status_code == 201


def test_a_required_role_field_cannot_be_cleared(client, owner):
    role = new_role(client, owner)
    path = f"{PERSONAL_ROLES}/{role['id']}"
    for field in ("slug", "name", "category"):
        assert (
            client.patch(path, headers=owner, json={field: None}).status_code == 422
        ), field


def test_every_role_link_must_point_at_a_role_that_exists(client, owner):
    for path, id_field in LINK_PATHS.values():
        body = {"personal_role_id": 987654321, id_field: 1}
        refused = client.post(path, headers=owner, json=body)
        assert refused.status_code == 422, (path, refused.text)


def test_every_role_link_needs_a_role_and_a_target(client, owner):
    role = new_role(client, owner)
    for path, id_field in LINK_PATHS.values():
        no_target = client.post(
            path, headers=owner, json={"personal_role_id": role["id"]}
        )
        assert no_target.status_code == 422, (path, "target")
        no_role = client.post(path, headers=owner, json={id_field: 1})
        assert no_role.status_code == 422, (path, "role")


def test_a_role_link_cannot_point_at_a_role_of_another_workspace(
    client, owner, harness, platform
):
    foreign = new_role(client, other_workspace(harness, platform))
    for path, id_field in LINK_PATHS.values():
        body = {"personal_role_id": foreign["id"], id_field: 1}
        refused = client.post(path, headers=owner, json=body)
        assert refused.status_code == 422, (path, refused.text)


def test_link_kinds_must_be_known(client, owner):
    role = new_role(client, owner)
    context = client.post(
        CONTEXT_LINKS,
        headers=owner,
        json={"personal_role_id": role["id"], "context_id": 1, "relation_type": "owns"},
    )
    assert context.status_code == 422
    for path, id_field in (
        LINK_PATHS["goal"],
        LINK_PATHS["project"],
        LINK_PATHS["task"],
    ):
        refused = client.post(
            path,
            headers=owner,
            json={"personal_role_id": role["id"], id_field: 1, "link_type": "owner"},
        )
        assert refused.status_code == 422, path


def test_link_source_is_limited_to_200_characters(client, owner):
    role = new_role(client, owner)
    for path, id_field in LINK_PATHS.values():
        refused = client.post(
            path,
            headers=owner,
            json={"personal_role_id": role["id"], id_field: 1, "source": "s" * 201},
        )
        assert refused.status_code == 422, path


def test_a_role_goal_link_needs_a_role_id_and_a_goal(client, owner):
    no_goal = client.post(ROLE_GOAL_LINKS, headers=owner, json={"role_id": unique("R")})
    assert no_goal.status_code == 422
    no_role = client.post(ROLE_GOAL_LINKS, headers=owner, json={"goal_id": 1})
    assert no_role.status_code == 422


def test_role_goal_link_limits_and_kinds(client, owner):
    base = {"role_id": unique("R"), "goal_id": 1}
    assert (
        client.post(
            ROLE_GOAL_LINKS, headers=owner, json={**base, "role_id": "r" * 201}
        ).status_code
        == 422
    )
    assert (
        client.post(
            ROLE_GOAL_LINKS, headers=owner, json={**base, "link_type": "owner"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            ROLE_GOAL_LINKS, headers=owner, json={**base, "priority": "high"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            ROLE_GOAL_LINKS, headers=owner, json={**base, "link_type": "supporting"}
        ).status_code
        == 201
    )
