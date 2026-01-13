import os
from dotenv import load_dotenv

from config.models import get_llm_key

load_dotenv()


class WorkflowConfig:
    """Configuration for NL2SQL workflow."""
    
    # Monitoring settings
    ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    EXPORT_METRICS = os.getenv("EXPORT_METRICS", "true").lower() == "true"
    METRICS_FILE = os.getenv("METRICS_FILE", "nl2sql_metrics.json")
    
    # LLM settings
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
    
    # Retry settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Vector search settings
    VECTOR_SEARCH_K = int(os.getenv("VECTOR_SEARCH_K", "5"))
    
    @classmethod
    def get_llm_key(cls):
        """Get LLM key in format provider:model."""
        return get_llm_key()
