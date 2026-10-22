"""Listing, grouping and the lifecycle of categories, skills and what refers to them."""

from roles_skills_helpers import (
    PROGRESS_LOG,
    ROLE_PATH_STEPS,
    ROLE_SKILL_LINKS,
    SKILL_CATEGORIES,
    SKILLS,
    create_progress,
    create_skill_link,
    create_step,
    new_category,
    new_skill,
    unique,
)


def test_categories_are_listed_by_sort_order(client, owner):
    parent = new_category(client, owner)
    third = new_category(client, owner, parent_id=parent["id"], sort_order=30)
    first = new_category(client, owner, parent_id=parent["id"], sort_order=10)
    second = new_category(client, owner, parent_id=parent["id"], sort_order=20)
    listed = client.get(
        SKILL_CATEGORIES, headers=owner, params={"parent_id": parent["id"]}
    )
    assert [c["id"] for c in listed.json()["items"]] == [
        first["id"],
        second["id"],
        third["id"],
    ]
    newest_first = client.get(
        SKILL_CATEGORIES,
        headers=owner,
        params={"parent_id": parent["id"], "order": "desc"},
    )
    assert [c["id"] for c in newest_first.json()["items"]] == [
        third["id"],
        second["id"],
        first["id"],
    ]


def test_category_stats_group_by_parent_and_refuse_other_fields(client, owner):
    parent = new_category(client, owner)
    new_category(client, owner, parent_id=parent["id"])
    new_category(client, owner, parent_id=parent["id"])
    stats = client.get(
        f"{SKILL_CATEGORIES}/stats", headers=owner, params={"group_by": "parent_id"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"][str(parent["id"])] == 2
    refused = client.get(
        f"{SKILL_CATEGORIES}/stats", headers=owner, params={"group_by": "name"}
    )
    assert refused.status_code == 422


def test_a_category_with_children_or_skills_cannot_be_deleted(client, owner):
    parent = new_category(client, owner)
    child = new_category(client, owner, parent_id=parent["id"])
    skill = new_skill(client, owner, category_id=child["id"])
    blocked_parent = client.delete(f"{SKILL_CATEGORIES}/{parent['id']}", headers=owner)
    assert blocked_parent.status_code == 409, blocked_parent.text
    blocked_child = client.delete(f"{SKILL_CATEGORIES}/{child['id']}", headers=owner)
    assert blocked_child.status_code == 409, blocked_child.text
    assert client.delete(f"{SKILLS}/{skill['id']}", headers=owner).status_code == 204
    assert (
        client.delete(f"{SKILL_CATEGORIES}/{child['id']}", headers=owner).status_code
        == 204
    )
    assert (
        client.delete(f"{SKILL_CATEGORIES}/{parent['id']}", headers=owner).status_code
        == 204
    )


def test_list_filters_skills_by_category_level_status_and_priority(client, owner):
    category = new_category(client, owner)
    mine = new_skill(
        client,
        owner,
        category_id=category["id"],
        level="L2_capable",
        target_level="L1_deep",
        status="practicing",
        priority=1,
    )
    new_skill(client, owner, category_id=category["id"], level="L4_outsource")
    for params in (
        {"category_id": category["id"], "level": "L2_capable"},
        {"category_id": category["id"], "target_level": "L1_deep"},
        {"category_id": category["id"], "status": "practicing"},
        {"category_id": category["id"], "priority": 1},
    ):
        listed = client.get(SKILLS, headers=owner, params=params)
        assert [s["id"] for s in listed.json()["items"]] == [mine["id"]], params


def test_list_filters_skills_by_revenue_relevance(client, owner):
    category = new_category(client, owner)
    paid = new_skill(client, owner, category_id=category["id"], revenue_relevant=True)
    new_skill(client, owner, category_id=category["id"], revenue_relevant=False)
    listed = client.get(
        SKILLS,
        headers=owner,
        params={"category_id": category["id"], "revenue_relevant": "true"},
    )
    assert [s["id"] for s in listed.json()["items"]] == [paid["id"]]
    not_a_boolean = client.get(
        SKILLS, headers=owner, params={"revenue_relevant": "yes"}
    )
    assert not_a_boolean.status_code == 422


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    assert (
        client.get(SKILLS, headers=owner, params={"name": "Python"}).status_code == 422
    )


def test_skill_stats_count_per_status_and_refuse_other_fields(client, owner):
    new_skill(client, owner, status="expert")
    stats = client.get(f"{SKILLS}/stats", headers=owner, params={"group_by": "status"})
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["expert"] >= 1
    refused = client.get(f"{SKILLS}/stats", headers=owner, params={"group_by": "slug"})
    assert refused.status_code == 422


def test_practising_a_skill_bumps_the_version_and_keeps_its_hours(client, owner):
    skill = new_skill(client, owner, hours_invested=10)
    path = f"{SKILLS}/{skill['id']}"
    practised = client.patch(
        path,
        headers=owner,
        json={
            "status": "practicing",
            "progress_percent": 30,
            "last_practiced": "2026-10-20",
        },
    )
    assert practised.status_code == 200, practised.text
    assert practised.json()["version"] == 2
    assert practised.json()["hours_invested"] == 10
    unchanged = client.patch(path, headers=owner, json={"progress_percent": 30})
    assert unchanged.json()["version"] == 2


def test_a_required_skill_field_cannot_be_cleared(client, owner):
    skill = new_skill(client, owner)
    path = f"{SKILLS}/{skill['id']}"
    for field in ("name", "slug"):
        assert (
            client.patch(path, headers=owner, json={field: None}).status_code == 422
        ), field


def test_a_skill_in_use_cannot_be_deleted(client, owner):
    skill = new_skill(client, owner)
    path = f"{SKILLS}/{skill['id']}"
    link = create_skill_link(client, owner, skill_id=skill["id"]).json()
    blocked = client.delete(path, headers=owner)
    assert blocked.status_code == 409, blocked.text
    assert blocked.json()["detail"] == {"error": "has_dependents"}
    assert (
        client.delete(f"{ROLE_SKILL_LINKS}/{link['id']}", headers=owner).status_code
        == 204
    )
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_role_skill_links_are_listed_by_role_skill_and_type(client, owner):
    skill = new_skill(client, owner)
    role = unique("ROLE")
    core = create_skill_link(client, owner, role_id=role, skill_id=skill["id"]).json()
    other = new_skill(client, owner)
    supporting = create_skill_link(
        client, owner, role_id=role, skill_id=other["id"], link_type="supporting"
    ).json()
    by_role = client.get(ROLE_SKILL_LINKS, headers=owner, params={"role_id": role})
    assert {x["id"] for x in by_role.json()["items"]} == {core["id"], supporting["id"]}
    by_type = client.get(
        ROLE_SKILL_LINKS, headers=owner, params={"role_id": role, "link_type": "core"}
    )
    assert [x["id"] for x in by_type.json()["items"]] == [core["id"]]
    by_skill = client.get(
        ROLE_SKILL_LINKS, headers=owner, params={"skill_id": other["id"]}
    )
    assert [x["id"] for x in by_skill.json()["items"]] == [supporting["id"]]


def test_path_steps_are_listed_by_role_phase_skill_and_registry(client, owner):
    role = unique("ROLE")
    skill = new_skill(client, owner)
    learn = create_step(
        client, owner, role_id=role, phase_id="learn", skill_id=skill["id"]
    ).json()
    practice = create_step(
        client,
        owner,
        role_id=role,
        phase_id="practice",
        source_registry="docs/OTHER.yaml",
    ).json()
    by_role = client.get(ROLE_PATH_STEPS, headers=owner, params={"role_id": role})
    assert {x["id"] for x in by_role.json()["items"]} == {learn["id"], practice["id"]}
    by_phase = client.get(
        ROLE_PATH_STEPS, headers=owner, params={"role_id": role, "phase_id": "practice"}
    )
    assert [x["id"] for x in by_phase.json()["items"]] == [practice["id"]]
    by_skill = client.get(
        ROLE_PATH_STEPS, headers=owner, params={"skill_id": skill["id"]}
    )
    assert [x["id"] for x in by_skill.json()["items"]] == [learn["id"]]
    by_registry = client.get(
        ROLE_PATH_STEPS,
        headers=owner,
        params={"role_id": role, "source_registry": "docs/OTHER.yaml"},
    )
    assert [x["id"] for x in by_registry.json()["items"]] == [practice["id"]]


def test_path_step_stats_group_by_phase_and_refuse_other_fields(client, owner):
    create_step(client, owner, phase_id="evidence")
    stats = client.get(
        f"{ROLE_PATH_STEPS}/stats", headers=owner, params={"group_by": "phase_id"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["evidence"] >= 1
    refused = client.get(
        f"{ROLE_PATH_STEPS}/stats", headers=owner, params={"group_by": "title"}
    )
    assert refused.status_code == 422


def test_progress_entries_are_listed_by_skill_and_activity(client, owner):
    skill = new_skill(client, owner)
    study = create_progress(
        client, owner, skill_id=skill["id"], activity_type="study", hours_spent=1.5
    ).json()
    create_progress(client, owner, skill_id=skill["id"], activity_type="teaching")
    by_skill = client.get(PROGRESS_LOG, headers=owner, params={"skill_id": skill["id"]})
    assert len(by_skill.json()["items"]) == 2
    only_study = client.get(
        PROGRESS_LOG,
        headers=owner,
        params={"skill_id": skill["id"], "activity_type": "study"},
    )
    assert [x["id"] for x in only_study.json()["items"]] == [study["id"]]
    assert only_study.json()["items"][0]["hours_spent"] == 1.5


def test_progress_stats_group_by_activity_and_refuse_other_fields(client, owner):
    create_progress(client, owner, activity_type="review")
    stats = client.get(
        f"{PROGRESS_LOG}/stats", headers=owner, params={"group_by": "activity_type"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["review"] >= 1
    refused = client.get(
        f"{PROGRESS_LOG}/stats", headers=owner, params={"group_by": "title"}
    )
    assert refused.status_code == 422


def test_a_progress_entry_can_be_corrected_and_deleted(client, owner):
    entry = create_progress(client, owner, progress_before=10, progress_after=20).json()
    path = f"{PROGRESS_LOG}/{entry['id']}"
    fixed = client.patch(path, headers=owner, json={"progress_after": 25})
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["version"] == 2
    assert (
        client.patch(path, headers=owner, json={"progress_after": 125}).status_code
        == 422
    )
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
