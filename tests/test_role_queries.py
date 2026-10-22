"""Listing, grouping and the lifecycle of roles and their links."""

from roles_skills_helpers import (
    CONTEXT_LINKS,
    GOAL_LINKS,
    PERSONAL_ROLES,
    PROJECT_LINKS,
    ROLE_GOAL_LINKS,
    TASK_LINKS,
    make,
    new_role,
    unique,
)


def test_list_filters_roles_by_category_and_status(client, owner):
    category = unique("cat")
    paused = new_role(client, owner, category=category, status="paused")
    new_role(client, owner, category=category, status="active")
    by_category = client.get(
        PERSONAL_ROLES, headers=owner, params={"category": category}
    )
    assert len(by_category.json()["items"]) == 2
    both = client.get(
        PERSONAL_ROLES, headers=owner, params={"category": category, "status": "paused"}
    )
    assert [r["id"] for r in both.json()["items"]] == [paused["id"]]


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(PERSONAL_ROLES, headers=owner, params={"slug": "anything"})
    assert listed.status_code == 422


def test_stats_count_roles_per_status_and_category(client, owner):
    category = unique("cat")
    new_role(client, owner, category=category, status="planned")
    new_role(client, owner, category=category, status="planned")
    by_status = client.get(
        f"{PERSONAL_ROLES}/stats", headers=owner, params={"group_by": "status"}
    )
    assert by_status.status_code == 200, by_status.text
    assert by_status.json()["groups"]["planned"] >= 2
    by_category = client.get(
        f"{PERSONAL_ROLES}/stats", headers=owner, params={"group_by": "category"}
    )
    assert by_category.json()["groups"][category] == 2


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{PERSONAL_ROLES}/stats", headers=owner, params={"group_by": "name"}
    )
    assert stats.status_code == 422


def test_retiring_a_role_bumps_the_version_once(client, owner):
    role = new_role(client, owner)
    path = f"{PERSONAL_ROLES}/{role['id']}"
    retired = client.patch(path, headers=owner, json={"status": "retired"})
    assert retired.status_code == 200, retired.text
    assert retired.json()["version"] == 2
    unchanged = client.patch(path, headers=owner, json={"status": "retired"})
    assert unchanged.json()["version"] == 2


def test_links_are_listed_per_role_and_target(client, owner):
    role, other = new_role(client, owner), new_role(client, owner)
    for path, id_field in (
        (CONTEXT_LINKS, "context_id"),
        (GOAL_LINKS, "goal_id"),
        (PROJECT_LINKS, "project_id"),
        (TASK_LINKS, "task_id"),
    ):
        mine = make(client, owner, path, personal_role_id=role["id"], **{id_field: 31})
        make(client, owner, path, personal_role_id=other["id"], **{id_field: 31})
        by_role = client.get(
            path, headers=owner, params={"personal_role_id": role["id"]}
        )
        assert [x["id"] for x in by_role.json()["items"]] == [mine["id"]], path
        by_target = client.get(path, headers=owner, params={id_field: 31})
        assert len(by_target.json()["items"]) >= 2, path


def test_link_stats_count_link_types_and_refuse_other_fields(client, owner):
    role = new_role(client, owner)
    make(
        client,
        owner,
        GOAL_LINKS,
        personal_role_id=role["id"],
        goal_id=1,
        link_type="supporting",
    )
    stats = client.get(
        f"{GOAL_LINKS}/stats", headers=owner, params={"group_by": "link_type"}
    )
    assert stats.json()["groups"]["supporting"] >= 1
    refused = client.get(
        f"{GOAL_LINKS}/stats", headers=owner, params={"group_by": "source"}
    )
    assert refused.status_code == 422


def test_a_role_with_links_cannot_be_deleted(client, owner):
    role = new_role(client, owner)
    path = f"{PERSONAL_ROLES}/{role['id']}"
    link = make(client, owner, TASK_LINKS, personal_role_id=role["id"], task_id=1)
    blocked = client.delete(path, headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == {"error": "has_dependents"}
    assert client.delete(f"{TASK_LINKS}/{link['id']}", headers=owner).status_code == 204
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_role_goal_links_are_listed_by_role_goal_and_type(client, owner):
    role_id = unique("R")
    primary = make(client, owner, ROLE_GOAL_LINKS, role_id=role_id, goal_id=1)
    support = make(
        client,
        owner,
        ROLE_GOAL_LINKS,
        role_id=role_id,
        goal_id=2,
        link_type="supporting",
    )
    by_role = client.get(ROLE_GOAL_LINKS, headers=owner, params={"role_id": role_id})
    assert {x["id"] for x in by_role.json()["items"]} == {primary["id"], support["id"]}
    by_type = client.get(
        ROLE_GOAL_LINKS,
        headers=owner,
        params={"role_id": role_id, "link_type": "supporting"},
    )
    assert [x["id"] for x in by_type.json()["items"]] == [support["id"]]
    by_goal = client.get(ROLE_GOAL_LINKS, headers=owner, params={"goal_id": 2})
    assert support["id"] in [x["id"] for x in by_goal.json()["items"]]


def test_a_role_goal_link_can_be_reweighted(client, owner):
    link = make(client, owner, ROLE_GOAL_LINKS, role_id=unique("R"), goal_id=1)
    path = f"{ROLE_GOAL_LINKS}/{link['id']}"
    changed = client.patch(
        path, headers=owner, json={"priority": 1, "allocation_percent": 60}
    )
    assert changed.status_code == 200, changed.text
    assert (changed.json()["priority"], changed.json()["allocation_percent"]) == (1, 60)
    assert changed.json()["version"] == 2
    assert client.delete(path, headers=owner).status_code == 204
