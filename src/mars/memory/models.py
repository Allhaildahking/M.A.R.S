"""Memory data models.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Memory:
    id: int | None
    content: str
    category: str = "general"
