"""Defaults and uniqueness of categories, skills, role-skill links, steps and progress entries."""

from roles_skills_helpers import (
    PROGRESS_LOG,
    SKILLS,
    create_category,
    create_progress,
    create_skill,
    create_skill_link,
    create_step,
    new_category,
    new_skill,
    unique,
)


def test_new_category_sorts_first_and_has_no_parent(client, owner):
    category = new_category(client, owner)
    assert category["sort_order"] == 0
    assert category["parent_id"] is None
    assert category["version"] == 1


def test_category_name_is_unique(client, owner):
    name = unique("name")
    assert create_category(client, owner, name=name).status_code == 201
    assert create_category(client, owner, name=name).status_code == 409


def test_category_slug_is_unique(client, owner):
    slug = unique("slug")
    assert create_category(client, owner, slug=slug).status_code == 201
    assert create_category(client, owner, slug=slug).status_code == 409


def test_a_category_can_be_nested(client, owner):
    parent = new_category(client, owner)
    child = create_category(client, owner, parent_id=parent["id"])
    assert child.status_code == 201, child.text
    assert child.json()["parent_id"] == parent["id"]


def test_new_skill_has_not_started_and_has_no_progress(client, owner):
    response = create_skill(client, owner)
    assert response.status_code == 201, response.text
    skill = response.json()
    assert skill["status"] == "not_started"
    assert skill["priority"] == 3
    assert skill["progress_percent"] == 0
    assert skill["hours_invested"] == 0
    assert skill["revenue_relevant"] is False
    assert skill["level"] is None
    assert skill["target_level"] is None
    assert skill["category_id"] is None
    assert skill["version"] == 1


def test_skill_slug_is_unique_but_names_may_repeat(client, owner):
    slug = unique("taken")
    assert create_skill(client, owner, slug=slug).status_code == 201
    assert create_skill(client, owner, slug=slug).status_code == 409
    assert create_skill(client, owner, name="Python").status_code == 201


def test_skill_import_keeps_the_old_id(client, owner):
    imported = create_skill(client, owner, legacy_id=2468)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 2468
    found = client.get(f"{SKILLS}/legacy/2468", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 2468
    assert create_skill(client, owner, legacy_id=2468).status_code == 409


def test_hours_invested_keeps_its_decimal_value(client, owner):
    skill = new_skill(client, owner, hours_invested=7.25)
    assert skill["hours_invested"] == 7.25


def test_new_role_skill_link_is_core_with_the_default_registry(client, owner):
    skill = new_skill(client, owner)
    response = create_skill_link(client, owner, skill_id=skill["id"])
    assert response.status_code == 201, response.text
    assert response.json()["link_type"] == "core"
    assert response.json()["source_registry"] == "docs/ROLE-LEARNING.yaml"


def test_a_role_links_to_a_skill_only_once(client, owner):
    skill, other = new_skill(client, owner), new_skill(client, owner)
    role = unique("ROLE")
    assert (
        create_skill_link(client, owner, role_id=role, skill_id=skill["id"]).status_code
        == 201
    )
    again = create_skill_link(client, owner, role_id=role, skill_id=skill["id"])
    assert again.status_code == 409
    assert (
        create_skill_link(client, owner, role_id=role, skill_id=other["id"]).status_code
        == 201
    )
    assert create_skill_link(client, owner, skill_id=skill["id"]).status_code == 201


def test_new_path_step_uses_the_default_registry(client, owner):
    response = create_step(client, owner)
    assert response.status_code == 201, response.text
    step = response.json()
    assert step["source_registry"] == "docs/ROLE-PATHS.yaml"
    assert step["skill_id"] is None
    assert step["target_progress"] is None
    assert step["version"] == 1


def test_a_role_step_key_is_unique_within_a_registry(client, owner):
    role, key = unique("ROLE"), unique("step")
    assert create_step(client, owner, role_id=role, step_key=key).status_code == 201
    assert create_step(client, owner, role_id=role, step_key=key).status_code == 409
    other_registry = create_step(
        client, owner, role_id=role, step_key=key, source_registry="docs/OTHER.yaml"
    )
    assert other_registry.status_code == 201, other_registry.text
    other_role = create_step(client, owner, step_key=key)
    assert other_role.status_code == 201, other_role.text


def test_new_progress_entry_is_an_other_activity(client, owner):
    response = create_progress(client, owner)
    assert response.status_code == 201, response.text
    entry = response.json()
    assert entry["activity_type"] == "other"
    assert entry["skill_id"] is None
    assert entry["hours_spent"] is None
    assert entry["logged_at"] is None
    assert entry["version"] == 1


def test_the_same_practice_can_be_logged_twice(client, owner):
    skill = new_skill(client, owner)
    for _ in range(2):
        entry = create_progress(client, owner, skill_id=skill["id"], title="Same")
        assert entry.status_code == 201, entry.text


def test_progress_import_keeps_the_old_id(client, owner):
    imported = create_progress(client, owner, legacy_id=1357)
    assert imported.status_code == 201, imported.text
    found = client.get(f"{PROGRESS_LOG}/legacy/1357", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["id"] == 1357
