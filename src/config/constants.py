"""Configuration constants for NLDBQ application."""
import os
from typing import Final

# Application Constants
APP_NAME: Final[str] = "NLDBQ"
APP_VERSION: Final[str] = "0.1.0"

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

# LLM Settings
DEFAULT_TEMPERATURE: Final[float] = 0.0
MAX_RETRIES: Final[int] = int(os.getenv("MAX_RETRIES", "3"))

# Vector Search
VECTOR_SEARCH_K: Final[int] = int(os.getenv("VECTOR_SEARCH_K", "5"))
VECTOR_STORE_PATH: Final[str] = "src/vectors/db_schema_vectors"

# SQL Safety
SQL_ROW_LIMIT: Final[int] = 10
FORBIDDEN_SQL_KEYWORDS: Final[tuple] = ("DELETE", "DROP", "TRUNCATE", "UPDATE", "INSERT", "ALTER")

# UI Settings
STREAMLIT_PORT: Final[int] = int(os.getenv("STREAMLIT_PORT", "8501"))
MAX_CHAT_HISTORY: Final[int] = 50
