"""
Utility functions for LangGraph agent workflow UI.
"""
import re
from typing import Optional, Dict, Any

def format_sql_query(sql: str) -> str:
    """Format SQL query for display."""
    if not sql:
        return ""
    
    # Remove common markdown code block markers
    sql = re.sub(r'^```sql\s*|```\s*$', '', sql, flags=re.IGNORECASE).strip()
    
    # Basic SQL formatting (capitalize keywords)
    keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
                'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'TOP', 'AS', 'ON', 'AND', 'OR']
    
    formatted = sql
    for keyword in keywords:
        pattern = re.compile(r'\b' + keyword + r'\b', re.IGNORECASE)
        formatted = pattern.sub(keyword, formatted)
    
    return formatted

def extract_sql_from_result(result: Dict[str, Any]) -> Optional[str]:
    """Extract SQL query from result dictionary."""
    if not result:
        return None
    
    # Try to get SQL from common keys
    sql = result.get('generated_query') or result.get('sql') or result.get('query')
    
    if sql:
        return format_sql_query(sql)
    
    return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "..."
