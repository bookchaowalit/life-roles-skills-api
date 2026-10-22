"""Defaults and uniqueness of personal roles and the links around them."""

from roles_skills_helpers import (
    CONTEXT_LINKS,
    GOAL_LINKS,
    PERSONAL_ROLES,
    PROJECT_LINKS,
    ROLE_GOAL_LINKS,
    TASK_LINKS,
    create_role,
    make,
    new_role,
    unique,
)


def test_new_role_is_active_and_manual(client, owner):
    response = create_role(client, owner)
    assert response.status_code == 201, response.text
    role = response.json()
    assert role["status"] == "active"
    assert role["source"] == "manual"
    assert role["description"] is None
    assert role["version"] == 1


def test_role_slug_is_unique(client, owner):
    slug = unique("taken")
    assert create_role(client, owner, slug=slug).status_code == 201
    assert create_role(client, owner, slug=slug, name="Another name").status_code == 409


def test_roles_may_share_a_name_and_category(client, owner):
    assert create_role(client, owner, name="Same", category="family").status_code == 201
    assert create_role(client, owner, name="Same", category="family").status_code == 201


def test_role_import_keeps_the_old_id(client, owner):
    imported = create_role(client, owner, legacy_id=321)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 321
    found = client.get(f"{PERSONAL_ROLES}/legacy/321", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 321
    assert create_role(client, owner, legacy_id=321).status_code == 409


def test_new_role_links_default_to_primary_or_belongs_to(client, owner):
    role = new_role(client, owner)
    ref = {"personal_role_id": role["id"]}
    context = make(client, owner, CONTEXT_LINKS, **ref, context_id=1)
    assert context["relation_type"] == "belongs_to"
    for path, id_field in (
        (GOAL_LINKS, "goal_id"),
        (PROJECT_LINKS, "project_id"),
        (TASK_LINKS, "task_id"),
    ):
        link = make(client, owner, path, **ref, **{id_field: 1})
        assert link["link_type"] == "primary", path
        assert link["source"] == "manual", path
        assert link["version"] == 1, path


def test_a_role_links_to_each_target_only_once(client, owner):
    role = new_role(client, owner)
    ref = {"personal_role_id": role["id"]}
    for path, id_field in (
        (CONTEXT_LINKS, "context_id"),
        (GOAL_LINKS, "goal_id"),
        (PROJECT_LINKS, "project_id"),
        (TASK_LINKS, "task_id"),
    ):
        make(client, owner, path, **ref, **{id_field: 5})
        again = client.post(path, headers=owner, json={**ref, id_field: 5})
        assert again.status_code == 409, path
        other_target = client.post(path, headers=owner, json={**ref, id_field: 6})
        assert other_target.status_code == 201, (path, other_target.text)


def test_the_same_target_can_link_to_several_roles(client, owner):
    first, second = new_role(client, owner), new_role(client, owner)
    for role in (first, second):
        link = client.post(
            GOAL_LINKS,
            headers=owner,
            json={"personal_role_id": role["id"], "goal_id": 77},
        )
        assert link.status_code == 201, link.text


def test_a_role_goal_link_defaults_to_primary_priority_3_and_no_share(client, owner):
    link = make(client, owner, ROLE_GOAL_LINKS, role_id=unique("R"), goal_id=1)
    assert link["link_type"] == "primary"
    assert link["priority"] == 3
    assert link["allocation_percent"] == 0
    assert link["source"] == "manual"


def test_a_role_id_links_to_a_goal_only_once(client, owner):
    role_id = unique("R")
    make(client, owner, ROLE_GOAL_LINKS, role_id=role_id, goal_id=9)
    again = client.post(
        ROLE_GOAL_LINKS, headers=owner, json={"role_id": role_id, "goal_id": 9}
    )
    assert again.status_code == 409
    other_goal = client.post(
        ROLE_GOAL_LINKS, headers=owner, json={"role_id": role_id, "goal_id": 10}
    )
    assert other_goal.status_code == 201, other_goal.text
