"""What a role-project allocation refuses: backwards dates, out-of-range numbers, bad enums."""

from roles_skills_helpers import ALLOCATIONS, create_allocation, unique


def test_an_allocation_cannot_end_before_it_starts(client, owner):
    backwards = create_allocation(
        client, owner, start_date="2026-06-30", end_date="2026-06-01"
    )
    assert backwards.status_code == 422, backwards.text
    assert backwards.json()["detail"] == {
        "error": "invalid_value",
        "fields": ["end_date", "start_date"],
    }
    same_day = create_allocation(
        client, owner, start_date="2026-06-01", end_date="2026-06-01"
    )
    assert same_day.status_code == 201, same_day.text


def test_moving_the_end_before_the_start_is_refused_on_update(client, owner):
    allocation = create_allocation(
        client, owner, start_date="2026-06-01", end_date="2026-06-30"
    ).json()
    path = f"{ALLOCATIONS}/{allocation['id']}"
    refused = client.patch(path, headers=owner, json={"end_date": "2026-05-31"})
    assert refused.status_code == 422, refused.text
    stored = client.get(path, headers=owner).json()
    assert stored["end_date"] == "2026-06-30"
    assert stored["version"] == 1
    # A patch that touches neither date still works.
    assert client.patch(path, headers=owner, json={"notes": "ok"}).status_code == 200


def test_an_open_ended_allocation_is_allowed(client, owner):
    only_start = create_allocation(client, owner, start_date="2026-06-01")
    only_end = create_allocation(client, owner, end_date="2026-06-01")
    assert only_start.status_code == 201, only_start.text
    assert only_end.status_code == 201, only_end.text


def test_role_id_and_project_id_are_required(client, owner):
    no_role = client.post(ALLOCATIONS, headers=owner, json={"project_id": 1})
    assert no_role.status_code == 422
    no_project = client.post(ALLOCATIONS, headers=owner, json={"role_id": unique("R")})
    assert no_project.status_code == 422


def test_role_id_is_limited_to_200_characters(client, owner):
    assert create_allocation(client, owner, role_id="r" * 201).status_code == 422
    assert create_allocation(client, owner, role_id="r" * 200).status_code == 201


def test_allocation_percent_stays_between_0_and_100(client, owner):
    assert create_allocation(client, owner, allocation_percent=-1).status_code == 422
    assert create_allocation(client, owner, allocation_percent=101).status_code == 422
    assert create_allocation(client, owner, allocation_percent=0).status_code == 201
    assert create_allocation(client, owner, allocation_percent=100).status_code == 201


def test_priority_stays_between_1_and_5(client, owner):
    assert create_allocation(client, owner, priority=0).status_code == 422
    assert create_allocation(client, owner, priority=6).status_code == 422
    assert create_allocation(client, owner, priority=1).status_code == 201
    assert create_allocation(client, owner, priority=5).status_code == 201


def test_status_must_be_a_known_state(client, owner):
    assert create_allocation(client, owner, status="done").status_code == 422
    assert create_allocation(client, owner, status="completed").status_code == 201


def test_source_is_limited_to_200_characters(client, owner):
    assert create_allocation(client, owner, source="s" * 201).status_code == 422


def test_dates_must_be_real_dates(client, owner):
    assert create_allocation(client, owner, start_date="soon").status_code == 422
    assert create_allocation(client, owner, end_date="2026-13-01").status_code == 422


def test_a_required_allocation_field_cannot_be_cleared(client, owner):
    allocation = create_allocation(client, owner).json()
    path = f"{ALLOCATIONS}/{allocation['id']}"
    for field in ("role_id", "project_id"):
        assert client.patch(path, headers=owner, json={field: None}).status_code == 422
