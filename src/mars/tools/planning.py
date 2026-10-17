"""Validated, non-executing task plans for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import ToolPermission, ToolResult, ToolSpec


@dataclass(frozen=True)
class PlanStep:
    """One proposed step in a task plan."""

    id: str
    title: str
    description: str
    depends_on: tuple[str, ...] = ()
    requires_approval: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "depends_on": list(self.depends_on),
            "requires_approval": self.requires_approval,
            "status": "pending",
        }


@dataclass(frozen=True)
class TaskPlan:
    """A validated plan. Creating a plan never runs its steps."""

    goal: str
    steps: tuple[PlanStep, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "status": "planned",
            "execution_policy": "plan_only",
            "steps": [step.as_dict() for step in self.steps],
            "note": "No steps have been executed.",
        }


def validate_task_plan(arguments: dict[str, Any]) -> TaskPlan:
    """Validate step fields, dependency references, and dependency cycles."""
    goal = arguments.get("goal")
    raw_steps = arguments.get("steps")
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be a non-empty string.")
    if len(goal) > 1000:
        raise ValueError("goal must be 1000 characters or fewer.")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("steps must be a non-empty list.")
    if len(raw_steps) > 30:
        raise ValueError("a plan may contain at most 30 steps.")

    steps: list[PlanStep] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise ValueError(f"step {index + 1} must be an object.")
        step_id = raw.get("id")
        title = raw.get("title")
        description = raw.get("description")
        dependencies = raw.get("depends_on", [])
        approval = raw.get("requires_approval", False)
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError(f"step {index + 1} needs a non-empty id.")
        if step_id in seen:
            raise ValueError(f"duplicate step id: {step_id}")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"step '{step_id}' needs a non-empty title.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"step '{step_id}' needs a non-empty description.")
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) and item.strip() for item in dependencies
        ):
            raise ValueError(f"step '{step_id}' depends_on must be a list of step ids.")
        if len(set(dependencies)) != len(dependencies):
            raise ValueError(f"step '{step_id}' contains duplicate dependencies.")
        if not isinstance(approval, bool):
            raise ValueError(f"step '{step_id}' requires_approval must be a boolean.")
        if step_id in dependencies:
            raise ValueError(f"step '{step_id}' cannot depend on itself.")
        if len(title) > 200 or len(description) > 2000:
            raise ValueError(f"step '{step_id}' exceeds the text length limit.")
        steps.append(
            PlanStep(
                id=step_id,
                title=title.strip(),
                description=description.strip(),
                depends_on=tuple(dependencies),
                requires_approval=approval,
            )
        )
        seen.add(step_id)

    for step in steps:
        for dependency in step.depends_on:
            if dependency not in seen:
                raise ValueError(
                    f"step '{step.id}' depends on unknown step '{dependency}'."
                )

    dependencies_by_id = {step.id: set(step.depends_on) for step in steps}
    resolved: set[str] = set()
    while len(resolved) < len(steps):
        ready = {
            step_id
            for step_id, dependencies in dependencies_by_id.items()
            if step_id not in resolved and dependencies <= resolved
        }
        if not ready:
            raise ValueError("plan dependencies contain a cycle.")
        resolved.update(ready)

    return TaskPlan(goal=goal.strip(), steps=tuple(steps))


@dataclass(frozen=True)
class CreateTaskPlanTool:
    """Validate and format a proposed plan without executing or storing it."""

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="create_task_plan",
            description=(
                "Validate a proposed task plan with dependencies. This only drafts a plan; "
                "it does not execute steps, modify files, or perform external actions."
            ),
            permission=ToolPermission.READ,
            input_schema={
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "minLength": 1, "maxLength": 1000},
                    "steps": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 30,
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "depends_on": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "requires_approval": {"type": "boolean"},
                            },
                            "required": ["id", "title", "description"],
                        },
                    },
                },
                "required": ["goal", "steps"],
            },
        )

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        try:
            plan = validate_task_plan(arguments)
        except ValueError as error:
            return ToolResult(success=False, error=str(error))
        return ToolResult(success=True, output=plan.as_dict())


def register_planning_tools(registry: Any) -> None:
    """Register non-executing planning capabilities with a tool registry."""
    registry.register(CreateTaskPlanTool())
