"""Tool contracts, registry, and research capabilities for MARS.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from .models import ModelTurn, Tool, ToolCall, ToolPermission, ToolResult, ToolSpec
from .planning import (
    CreateTaskPlanTool,
    PlanStep,
    TaskPlan,
    register_planning_tools,
    validate_task_plan,
)
from .registry import ToolRegistry
from .research import WebFetchTool, WebSearchTool, fetch_public_page, register_web_research_tools

__all__ = [
    "ModelTurn",
    "Tool",
    "ToolCall",
    "ToolPermission",
    "ToolResult",
    "ToolSpec",
    "ToolRegistry",
    "CreateTaskPlanTool",
    "PlanStep",
    "TaskPlan",
    "register_planning_tools",
    "validate_task_plan",
    "WebFetchTool",
    "WebSearchTool",
    "fetch_public_page",
    "register_web_research_tools",
]
