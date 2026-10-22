"""What skills, categories, role-skill links, path steps and progress entries refuse."""

from roles_skills_helpers import (
    PROGRESS_LOG,
    ROLE_PATH_STEPS,
    ROLE_SKILL_LINKS,
    SKILL_CATEGORIES,
    SKILLS,
    create_category,
    create_progress,
    create_skill,
    create_skill_link,
    create_step,
    new_category,
    new_skill,
    other_workspace,
    unique,
)

LEVELS = ["L1_deep", "L2_capable", "L3_overview", "L4_outsource"]


def test_a_category_needs_a_name_and_a_slug(client, owner):
    no_slug = client.post(SKILL_CATEGORIES, headers=owner, json={"name": unique("c")})
    assert no_slug.status_code == 422
    no_name = client.post(SKILL_CATEGORIES, headers=owner, json={"slug": unique("c")})
    assert no_name.status_code == 422


def test_category_text_limits(client, owner):
    assert create_category(client, owner, name="n" * 201).status_code == 422
    assert create_category(client, owner, slug="s" * 201).status_code == 422
    assert create_category(client, owner, icon="i" * 101).status_code == 422
    assert create_category(client, owner, color="c" * 41).status_code == 422
    assert (
        create_category(client, owner, icon="i" * 100, color="c" * 40).status_code
        == 201
    )


def test_a_category_parent_must_exist(client, owner):
    assert create_category(client, owner, parent_id=987654321).status_code == 422
    assert create_category(client, owner, parent_id=0).status_code == 422


def test_a_category_cannot_have_a_parent_from_another_workspace(
    client, owner, harness, platform
):
    foreign = new_category(client, other_workspace(harness, platform))
    assert create_category(client, owner, parent_id=foreign["id"]).status_code == 422


def test_a_skill_needs_a_name_and_a_slug(client, owner):
    assert client.post(SKILLS, headers=owner, json={"name": "Go"}).status_code == 422
    assert (
        client.post(SKILLS, headers=owner, json={"slug": unique("s")}).status_code
        == 422
    )


def test_skill_text_limits(client, owner):
    assert create_skill(client, owner, name="n" * 501).status_code == 422
    assert create_skill(client, owner, slug="s" * 201).status_code == 422
    assert (
        create_skill(client, owner, name="n" * 500, slug="s" * 200).status_code == 201
    )


def test_skill_levels_must_be_known(client, owner):
    for level in LEVELS:
        assert (
            create_skill(client, owner, level=level, target_level=level).status_code
            == 201
        ), level
    assert create_skill(client, owner, level="L5_master").status_code == 422
    assert create_skill(client, owner, target_level="expert").status_code == 422


def test_skill_status_must_be_a_known_state(client, owner):
    assert create_skill(client, owner, status="done").status_code == 422
    assert create_skill(client, owner, status="proficient").status_code == 201


def test_progress_percent_stays_between_0_and_100(client, owner):
    assert create_skill(client, owner, progress_percent=-1).status_code == 422
    assert create_skill(client, owner, progress_percent=101).status_code == 422
    assert create_skill(client, owner, progress_percent=0).status_code == 201
    assert create_skill(client, owner, progress_percent=100).status_code == 201


def test_progress_percent_is_checked_on_update_too(client, owner):
    skill = new_skill(client, owner, progress_percent=50)
    path = f"{SKILLS}/{skill['id']}"
    assert (
        client.patch(path, headers=owner, json={"progress_percent": 150}).status_code
        == 422
    )
    assert client.get(path, headers=owner).json()["progress_percent"] == 50


def test_a_skill_category_must_exist(client, owner):
    assert create_skill(client, owner, category_id=987654321).status_code == 422


def test_a_skill_cannot_use_a_category_of_another_workspace(
    client, owner, harness, platform
):
    foreign = new_category(client, other_workspace(harness, platform))
    assert create_skill(client, owner, category_id=foreign["id"]).status_code == 422


def test_skill_dates_must_be_real_dates(client, owner):
    assert create_skill(client, owner, started_at="last spring").status_code == 422
    assert create_skill(client, owner, last_practiced="2026-02-31").status_code == 422
    assert (
        create_skill(client, owner, target_completion_date="never").status_code == 422
    )


def test_hours_invested_must_be_a_number(client, owner):
    assert create_skill(client, owner, hours_invested="many").status_code == 422
    assert create_skill(client, owner, hours_invested=12.5).status_code == 201


def test_revenue_relevant_must_be_true_or_false(client, owner):
    assert create_skill(client, owner, revenue_relevant="maybe").status_code == 422
    assert create_skill(client, owner, revenue_relevant=True).status_code == 201


def test_a_role_skill_link_needs_a_role_a_skill_and_a_path(client, owner):
    skill = new_skill(client, owner)
    complete = {"role_id": unique("R"), "skill_id": skill["id"], "learning_path": "p"}
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        assert (
            client.post(ROLE_SKILL_LINKS, headers=owner, json=body).status_code == 422
        ), missing


def test_a_role_skill_link_must_point_at_a_skill_that_exists(client, owner):
    assert create_skill_link(client, owner, skill_id=987654321).status_code == 422


def test_a_role_skill_link_cannot_point_at_a_skill_of_another_workspace(
    client, owner, harness, platform
):
    foreign = new_skill(client, other_workspace(harness, platform))
    assert create_skill_link(client, owner, skill_id=foreign["id"]).status_code == 422


def test_role_skill_link_kind_and_limits(client, owner):
    skill = new_skill(client, owner)
    assert (
        create_skill_link(
            client, owner, skill_id=skill["id"], link_type="optional"
        ).status_code
        == 422
    )
    assert (
        create_skill_link(
            client, owner, skill_id=skill["id"], role_id="r" * 201
        ).status_code
        == 422
    )
    assert (
        create_skill_link(
            client, owner, skill_id=skill["id"], source_registry="p" * 301
        ).status_code
        == 422
    )
    assert (
        create_skill_link(
            client, owner, skill_id=skill["id"], link_type="supporting"
        ).status_code
        == 201
    )


def test_a_path_step_needs_its_identity_and_instructions(client, owner):
    complete = {
        "role_id": unique("R"),
        "step_key": unique("s"),
        "phase_id": "orient",
        "title": "t",
        "action": "a",
        "completion_rule": "c",
    }
    for missing in complete:
        body = {k: v for k, v in complete.items() if k != missing}
        assert (
            client.post(ROLE_PATH_STEPS, headers=owner, json=body).status_code == 422
        ), missing


def test_a_path_step_phase_must_be_known(client, owner):
    for phase in ("orient", "learn", "practice", "evidence", "operate"):
        assert create_step(client, owner, phase_id=phase).status_code == 201, phase
    assert create_step(client, owner, phase_id="finish").status_code == 422


def test_path_step_text_limits(client, owner):
    assert create_step(client, owner, role_id="r" * 201).status_code == 422
    assert create_step(client, owner, step_key="k" * 201).status_code == 422
    assert create_step(client, owner, title="t" * 501).status_code == 422
    assert create_step(client, owner, source_registry="p" * 301).status_code == 422


def test_target_progress_stays_between_0_and_100(client, owner):
    assert create_step(client, owner, target_progress=-1).status_code == 422
    assert create_step(client, owner, target_progress=101).status_code == 422
    assert create_step(client, owner, target_progress=100).status_code == 201


def test_a_path_step_skill_must_exist_in_this_workspace(
    client, owner, harness, platform
):
    assert create_step(client, owner, skill_id=987654321).status_code == 422
    foreign = new_skill(client, other_workspace(harness, platform))
    assert create_step(client, owner, skill_id=foreign["id"]).status_code == 422


def test_a_progress_entry_needs_a_title(client, owner):
    assert client.post(PROGRESS_LOG, headers=owner, json={}).status_code == 422
    assert create_progress(client, owner, title="").status_code == 422


def test_progress_entry_numbers_stay_in_range(client, owner):
    assert create_progress(client, owner, hours_spent=-0.5).status_code == 422
    assert create_progress(client, owner, progress_before=-1).status_code == 422
    assert create_progress(client, owner, progress_before=101).status_code == 422
    assert create_progress(client, owner, progress_after=101).status_code == 422
    ok = create_progress(
        client, owner, hours_spent=0, progress_before=0, progress_after=100
    )
    assert ok.status_code == 201, ok.text


def test_progress_entry_kind_and_limits(client, owner):
    assert create_progress(client, owner, activity_type="nap").status_code == 422
    assert create_progress(client, owner, title="t" * 501).status_code == 422
    assert create_progress(client, owner, evidence_url="u" * 2001).status_code == 422
    assert create_progress(client, owner, evidence_url="u" * 2000).status_code == 201
    assert create_progress(client, owner, logged_at="tonight").status_code == 422


def test_a_progress_entry_skill_must_exist_in_this_workspace(
    client, owner, harness, platform
):
    assert create_progress(client, owner, skill_id=987654321).status_code == 422
    foreign = new_skill(client, other_workspace(harness, platform))
    assert create_progress(client, owner, skill_id=foreign["id"]).status_code == 422
