"""Persistent, approval-gated task-plan lifecycle for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from .planning import validate_task_plan


class TaskPlanStore:
    """Persist plans and track step readiness without executing their actions."""

    def __init__(self, database_path: str = "data/mars_tasks.db") -> None:
        self.database_path = database_path
        self._connection: sqlite3.Connection | None = None
        if database_path == ":memory:":
            self._connection = sqlite3.connect(database_path)
            self._connection.row_factory = sqlite3.Row
        else:
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        connection = self._connect()
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_plans (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planned',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS task_steps (
                plan_id TEXT NOT NULL REFERENCES task_plans(id) ON DELETE CASCADE,
                step_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                depends_on TEXT NOT NULL,
                requires_approval INTEGER NOT NULL DEFAULT 0,
                approval_granted INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY (plan_id, step_id)
            )
            """
        )
        connection.commit()

    def create_plan(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate and persist a plan. No step is executed or started."""
        plan = validate_task_plan(arguments)
        plan_id = uuid4().hex
        connection = self._connect()
        try:
            connection.execute(
                "INSERT INTO task_plans (id, goal) VALUES (?, ?)",
                (plan_id, plan.goal),
            )
            for position, step in enumerate(plan.steps):
                connection.execute(
                    """
                    INSERT INTO task_steps (
                        plan_id, step_id, position, title, description, depends_on,
                        requires_approval
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_id,
                        step.id,
                        position,
                        step.title,
                        step.description,
                        json.dumps(list(step.depends_on)),
                        int(step.requires_approval),
                    ),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        result = self.get_plan(plan_id)
        assert result is not None
        return result

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        connection = self._connect()
        plan = connection.execute(
            """
            SELECT id, goal, status, created_at, updated_at
            FROM task_plans WHERE id = ?
            """,
            (plan_id,),
        ).fetchone()
        if plan is None:
            return None
        rows = connection.execute(
            """
            SELECT step_id, title, description, depends_on, requires_approval,
                   approval_granted, status
            FROM task_steps WHERE plan_id = ? ORDER BY position
            """,
            (plan_id,),
        ).fetchall()
        steps = []
        completed = {
            row["step_id"] for row in rows if row["status"] == "completed"
        }
        for row in rows:
            dependencies = json.loads(row["depends_on"])
            dependencies_complete = all(item in completed for item in dependencies)
            approval_required = bool(row["requires_approval"])
            approved = bool(row["approval_granted"])
            steps.append(
                {
                    "id": row["step_id"],
                    "title": row["title"],
                    "description": row["description"],
                    "depends_on": dependencies,
                    "requires_approval": approval_required,
                    "approval_granted": approved,
                    "status": row["status"],
                    "dependencies_complete": dependencies_complete,
                    "ready_to_start": (
                        row["status"] == "pending"
                        and dependencies_complete
                        and (not approval_required or approved)
                    ),
                    "blocked_reason": (
                        "dependencies_incomplete"
                        if row["status"] == "pending" and not dependencies_complete
                        else "approval_required"
                        if row["status"] == "pending"
                        and approval_required
                        and not approved
                        else None
                    ),
                }
            )
        return {
            "id": plan["id"],
            "goal": plan["goal"],
            "status": plan["status"],
            "created_at": plan["created_at"],
            "updated_at": plan["updated_at"],
            "execution_policy": "approval_gated",
            "steps": steps,
        }

    def list_plans(self, limit: int = 20) -> list[dict[str, Any]]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100.")
        connection = self._connect()
        rows = connection.execute(
            "SELECT id FROM task_plans ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            plan
            for row in rows
            if (plan := self.get_plan(row["id"])) is not None
        ]

    def approve_step(self, plan_id: str, step_id: str) -> dict[str, Any]:
        """Record explicit approval; this does not start or execute the step."""
        connection = self._connect()
        row = self._get_step(connection, plan_id, step_id)
        if row["status"] != "pending":
            raise ValueError("Only pending steps can be approved.")
        if not row["requires_approval"]:
            raise ValueError("This step does not require approval.")
        connection.execute(
            """
            UPDATE task_steps SET approval_granted = 1
            WHERE plan_id = ? AND step_id = ?
            """,
            (plan_id, step_id),
        )
        connection.execute(
            "UPDATE task_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (plan_id,),
        )
        connection.commit()
        result = self.get_plan(plan_id)
        assert result is not None
        return result

    def start_step(self, plan_id: str, step_id: str) -> dict[str, Any]:
        """Mark a ready step in progress, enforcing dependencies and approval."""
        connection = self._connect()
        row = self._get_step(connection, plan_id, step_id)
        if row["status"] != "pending":
            raise ValueError("Only pending steps can be started.")
        dependencies = json.loads(row["depends_on"])
        for dependency in dependencies:
            dependency_row = self._get_step(connection, plan_id, dependency)
            if dependency_row["status"] != "completed":
                raise ValueError(
                    f"Step '{step_id}' is blocked until dependency "
                    f"'{dependency}' is completed."
                )
        if row["requires_approval"] and not row["approval_granted"]:
            raise PermissionError(f"Step '{step_id}' requires explicit approval.")
        connection.execute(
            """
            UPDATE task_steps SET status = 'in_progress'
            WHERE plan_id = ? AND step_id = ?
            """,
            (plan_id, step_id),
        )
        connection.execute(
            """
            UPDATE task_plans SET status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (plan_id,),
        )
        connection.commit()
        result = self.get_plan(plan_id)
        assert result is not None
        return result

    def complete_step(self, plan_id: str, step_id: str) -> dict[str, Any]:
        """Mark a started step complete; this method performs no external action."""
        connection = self._connect()
        row = self._get_step(connection, plan_id, step_id)
        if row["status"] != "in_progress":
            raise ValueError("Only in-progress steps can be completed.")
        connection.execute(
            """
            UPDATE task_steps SET status = 'completed'
            WHERE plan_id = ? AND step_id = ?
            """,
            (plan_id, step_id),
        )
        remaining = connection.execute(
            """
            SELECT COUNT(*) AS count FROM task_steps
            WHERE plan_id = ? AND status != 'completed'
            """,
            (plan_id,),
        ).fetchone()["count"]
        status = "completed" if remaining == 0 else "in_progress"
        connection.execute(
            """
            UPDATE task_plans SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, plan_id),
        )
        connection.commit()
        result = self.get_plan(plan_id)
        assert result is not None
        return result

    @staticmethod
    def _get_step(
        connection: sqlite3.Connection,
        plan_id: str,
        step_id: str,
    ) -> sqlite3.Row:
        plan_exists = connection.execute(
            "SELECT 1 FROM task_plans WHERE id = ?", (plan_id,)
        ).fetchone()
        if plan_exists is None:
            raise KeyError(f"Unknown task plan: {plan_id}")
        row = connection.execute(
            """
            SELECT step_id, depends_on, requires_approval, approval_granted, status
            FROM task_steps WHERE plan_id = ? AND step_id = ?
            """,
            (plan_id, step_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown step '{step_id}' in plan '{plan_id}'.")
        return row

    def close(self) -> None:
        """Close the dedicated in-memory database connection, if present."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> TaskPlanStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
