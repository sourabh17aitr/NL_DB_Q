"""
Configuration settings for Vector DB UI
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import project configurations
from config.vector_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME

# UI specific configurations
UI_TITLE = "Vector DB Schema Explorer"
UI_ICON = "🗄️"

# Display settings
DEFAULT_RESULTS_COUNT = 5
MAX_RESULTS_COUNT = 10
CACHE_TTL = 300  # seconds

# Styling
THEME_PRIMARY_COLOR = "#1f77b4"
THEME_SECONDARY_COLOR = "#ff7f0e"

# Export configurations
__all__ = [
    'VECTOR_DB_SCHEMA_DIR',
    'VECTOR_DB_SCHEMA_NAME',
    'UI_TITLE',
    'UI_ICON',
    'DEFAULT_RESULTS_COUNT',
    'MAX_RESULTS_COUNT',
    'CACHE_TTL',
    'THEME_PRIMARY_COLOR',
    'THEME_SECONDARY_COLOR'
]
