"""Defaults and uniqueness of a role-project allocation."""

from roles_skills_helpers import ALLOCATIONS, create_allocation, unique


def test_new_allocation_is_planned_with_no_share_and_middle_priority(client, owner):
    response = create_allocation(client, owner)
    assert response.status_code == 201, response.text
    allocation = response.json()
    assert allocation["status"] == "planned"
    assert allocation["allocation_percent"] == 0
    assert allocation["priority"] == 3
    assert allocation["source"] == "manual"
    assert allocation["goal_id"] is None
    assert allocation["start_date"] is None
    assert allocation["end_date"] is None
    assert allocation["version"] == 1


def test_a_role_cannot_repeat_a_project_and_goal_pair(client, owner):
    role = unique("ROLE")
    assert (
        create_allocation(
            client, owner, role_id=role, project_id=7, goal_id=3
        ).status_code
        == 201
    )
    again = create_allocation(client, owner, role_id=role, project_id=7, goal_id=3)
    assert again.status_code == 409


def test_a_role_can_work_a_project_for_different_goals(client, owner):
    role = unique("ROLE")
    assert (
        create_allocation(
            client, owner, role_id=role, project_id=7, goal_id=3
        ).status_code
        == 201
    )
    other_goal = create_allocation(client, owner, role_id=role, project_id=7, goal_id=4)
    assert other_goal.status_code == 201, other_goal.text


def test_the_same_project_can_have_several_roles(client, owner):
    assert create_allocation(client, owner, project_id=8, goal_id=3).status_code == 201
    assert create_allocation(client, owner, project_id=8, goal_id=3).status_code == 201


def test_allocations_without_a_goal_are_not_deduplicated(client, owner):
    # The unique key includes goal_id, and the database treats empty values as different,
    # so a role may repeat a project while no goal is set.
    role = unique("ROLE")
    first = create_allocation(client, owner, role_id=role, project_id=9)
    second = create_allocation(client, owner, role_id=role, project_id=9)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text


def test_an_import_keeps_the_old_id_and_refuses_a_second_import(client, owner):
    imported = create_allocation(client, owner, legacy_id=1234)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 1234
    found = client.get(f"{ALLOCATIONS}/legacy/1234", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 1234
    assert create_allocation(client, owner, legacy_id=1234).status_code == 409
