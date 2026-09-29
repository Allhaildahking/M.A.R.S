"""Application configuration.

Copyright (c) 2026 Destiny Growrich. All rights reserved.
Project: MARS (Multifunctional Autonomous Reasoning System)
Provenance marker: MARS-DG-2026
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("MARS_ENV", "development")
    log_level: str = os.getenv("MARS_LOG_LEVEL", "INFO")
    database_url: str = os.getenv(
        "MARS_DATABASE_URL",
        "sqlite:///data/mars.db",
    )
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("MARS_GEMINI_MODEL", "gemini-3.8-flash")


settings = Settings()
