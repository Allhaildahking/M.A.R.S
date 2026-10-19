"""Tests for persistent, approval-gated task plans."""

import pytest

from mars.tools.task_state import TaskPlanStore


def plan_arguments() -> dict[str, object]:
    return {
        "goal": "Prepare and publish an update",
        "steps": [
            {
                "id": "draft",
                "title": "Draft update",
                "description": "Write the update.",
            },
            {
                "id": "publish",
                "title": "Publish update",
                "description": "Publish only after review and explicit approval.",
                "depends_on": ["draft"],
                "requires_approval": True,
            },
        ],
    }


def test_create_plan_persists_pending_steps_without_executing() -> None:
    with TaskPlanStore(":memory:") as store:
        plan = store.create_plan(plan_arguments())

        assert plan["status"] == "planned"
        assert plan["execution_policy"] == "approval_gated"
        assert plan["steps"][0]["status"] == "pending"
        assert plan["steps"][0]["ready_to_start"] is True
        assert plan["steps"][1]["ready_to_start"] is False
        assert plan["steps"][1]["blocked_reason"] == "dependencies_incomplete"


def test_cannot_start_dependent_step_before_dependency_is_completed() -> None:
    with TaskPlanStore(":memory:") as store:
        plan = store.create_plan(plan_arguments())

        with pytest.raises(ValueError, match="dependency 'draft' is completed"):
            store.start_step(plan["id"], "publish")


def test_approval_is_required_before_starting_consequential_step() -> None:
    with TaskPlanStore(":memory:") as store:
        plan = store.create_plan(plan_arguments())
        store.start_step(plan["id"], "draft")
        plan = store.complete_step(plan["id"], "draft")

        publish = plan["steps"][1]
        assert publish["dependencies_complete"] is True
        assert publish["ready_to_start"] is False
        assert publish["blocked_reason"] == "approval_required"

        with pytest.raises(PermissionError, match="requires explicit approval"):
            store.start_step(plan["id"], "publish")

        plan = store.approve_step(plan["id"], "publish")
        assert plan["steps"][1]["ready_to_start"] is True

        plan = store.start_step(plan["id"], "publish")
        assert plan["steps"][1]["status"] == "in_progress"
        assert plan["status"] == "in_progress"


def test_plan_completes_only_when_every_step_is_completed() -> None:
    with TaskPlanStore(":memory:") as store:
        plan = store.create_plan(plan_arguments())
        store.start_step(plan["id"], "draft")
        plan = store.complete_step(plan["id"], "draft")
        assert plan["status"] == "in_progress"

        store.approve_step(plan["id"], "publish")
        store.start_step(plan["id"], "publish")
        plan = store.complete_step(plan["id"], "publish")

        assert plan["status"] == "completed"
        assert all(step["status"] == "completed" for step in plan["steps"])


def test_plan_survives_store_restart(tmp_path) -> None:
    database_path = str(tmp_path / "tasks.sqlite3")
    with TaskPlanStore(database_path) as store:
        created = store.create_plan(plan_arguments())
        plan_id = created["id"]

    with TaskPlanStore(database_path) as reopened:
        loaded = reopened.get_plan(plan_id)

    assert loaded is not None
    assert loaded["goal"] == "Prepare and publish an update"
    assert [step["id"] for step in loaded["steps"]] == ["draft", "publish"]


def test_unknown_plan_and_step_are_rejected() -> None:
    with TaskPlanStore(":memory:") as store:
        with pytest.raises(KeyError, match="Unknown task plan"):
            store.start_step("missing", "draft")

        plan = store.create_plan(plan_arguments())
        with pytest.raises(KeyError, match="Unknown step"):
            store.start_step(plan["id"], "missing")


def test_non_approval_step_cannot_be_approved() -> None:
    with TaskPlanStore(":memory:") as store:
        plan = store.create_plan(plan_arguments())

        with pytest.raises(ValueError, match="does not require approval"):
            store.approve_step(plan["id"], "draft")
