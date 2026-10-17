"""Tests for non-executing MARS task planning."""

import pytest

from mars.tools import ToolPermission, ToolRegistry
from mars.tools.planning import CreateTaskPlanTool, validate_task_plan


def valid_arguments() -> dict[str, object]:
    return {
        "goal": "Publish a portfolio update",
        "steps": [
            {
                "id": "draft",
                "title": "Draft the update",
                "description": "Write a concise post.",
            },
            {
                "id": "review",
                "title": "Review the post",
                "description": "Check tone and links.",
                "depends_on": ["draft"],
                "requires_approval": True,
            },
        ],
    }


def test_valid_plan_keeps_dependencies_and_does_not_execute() -> None:
    result = CreateTaskPlanTool().execute(valid_arguments())

    assert result.success is True
    assert result.output["execution_policy"] == "plan_only"
    assert result.output["note"] == "No steps have been executed."
    assert result.output["steps"][1]["depends_on"] == ["draft"]
    assert result.output["steps"][1]["requires_approval"] is True
    assert all(step["status"] == "pending" for step in result.output["steps"])


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda args: args.update(goal=" "), "goal must be a non-empty string"),
        (lambda args: args.update(steps=[]), "steps must be a non-empty list"),
        (
            lambda args: args["steps"].append(dict(args["steps"][0])),
            "duplicate step id",
        ),
        (
            lambda args: args["steps"][0].update(depends_on=["missing"]),
            "unknown step",
        ),
        (
            lambda args: args["steps"][0].update(depends_on=["draft"]),
            "cannot depend on itself",
        ),
    ],
)
def test_invalid_plan_is_rejected(mutate, message: str) -> None:
    arguments = valid_arguments()
    mutate(arguments)
    with pytest.raises(ValueError, match=message):
        validate_task_plan(arguments)


def test_dependency_cycle_is_rejected() -> None:
    arguments = valid_arguments()
    arguments["steps"][0]["depends_on"] = ["review"]
    with pytest.raises(ValueError, match="contain a cycle"):
        validate_task_plan(arguments)


def test_plan_tool_requires_read_permission_when_registered() -> None:
    registry = ToolRegistry()
    registry.register(CreateTaskPlanTool())

    denied = registry.execute("create_task_plan", valid_arguments())
    allowed = registry.execute(
        "create_task_plan",
        valid_arguments(),
        allowed_permissions={ToolPermission.READ},
    )

    assert denied.success is False
    assert "Permission denied" in (denied.error or "")
    assert allowed.success is True
