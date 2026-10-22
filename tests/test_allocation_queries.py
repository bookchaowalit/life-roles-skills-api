"""Listing, grouping and the lifecycle of a role-project allocation."""

from roles_skills_helpers import ALLOCATIONS, create_allocation, unique


def test_list_filters_by_role_project_goal_and_status(client, owner):
    role = unique("ROLE")
    mine = create_allocation(
        client, owner, role_id=role, project_id=501, goal_id=11, status="active"
    ).json()
    create_allocation(client, owner, project_id=502, goal_id=12)
    for params in (
        {"role_id": role},
        {"project_id": 501},
        {"goal_id": 11},
        {"role_id": role, "status": "active"},
    ):
        listed = client.get(ALLOCATIONS, headers=owner, params=params)
        assert listed.status_code == 200, listed.text
        assert mine["id"] in [a["id"] for a in listed.json()["items"]], params
    none = client.get(
        ALLOCATIONS, headers=owner, params={"role_id": role, "status": "paused"}
    )
    assert none.json()["items"] == []


def test_list_can_ask_for_allocations_without_a_goal(client, owner):
    role = unique("ROLE")
    no_goal = create_allocation(client, owner, role_id=role, project_id=511).json()
    create_allocation(client, owner, role_id=role, project_id=512, goal_id=1)
    listed = client.get(
        ALLOCATIONS, headers=owner, params={"role_id": role, "null": "goal_id"}
    )
    assert [a["id"] for a in listed.json()["items"]] == [no_goal["id"]]


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(ALLOCATIONS, headers=owner, params={"priority": 3})
    assert listed.status_code == 422


def test_stats_count_allocations_per_status(client, owner):
    create_allocation(client, owner, status="active")
    create_allocation(client, owner, status="completed")
    stats = client.get(
        f"{ALLOCATIONS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["active"] >= 1
    assert stats.json()["groups"]["completed"] >= 1


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{ALLOCATIONS}/stats", headers=owner, params={"group_by": "priority"}
    )
    assert stats.status_code == 422


def test_completing_an_allocation_keeps_its_share_and_dates(client, owner):
    allocation = create_allocation(
        client,
        owner,
        status="active",
        allocation_percent=40,
        start_date="2026-06-01",
        end_date="2026-06-30",
    ).json()
    path = f"{ALLOCATIONS}/{allocation['id']}"
    done = client.patch(path, headers=owner, json={"status": "completed"})
    assert done.status_code == 200, done.text
    assert done.json()["version"] == 2
    assert done.json()["allocation_percent"] == 40
    assert done.json()["end_date"] == "2026-06-30"
    unchanged = client.patch(path, headers=owner, json={"status": "completed"})
    assert unchanged.json()["version"] == 2


def test_a_deleted_allocation_is_gone(client, owner):
    allocation = create_allocation(client, owner).json()
    path = f"{ALLOCATIONS}/{allocation['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
