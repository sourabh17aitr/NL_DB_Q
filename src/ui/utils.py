# Utility functions for message/chunk processing (extracted from main file)
from typing import Any, List

def safe_message_content(msg: Any) -> str:
    """Extract string from message or tool result - handles all LangGraph message types."""
    try:
        if hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, list) and content:
                return content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
            return str(content)
        elif hasattr(msg, 'lc_kwargs') and 'content' in msg.lc_kwargs:
            return str(msg.lc_kwargs['content'])  # ToolMessage
        elif isinstance(msg, dict) and 'content' in msg:
            return str(msg['content'])
        elif hasattr(msg, '__dict__'):
            return str(getattr(msg, 'content', str(msg)))
        return str(msg)
    except Exception:
        return str(msg)

def extract_content_from_chunk(chunk: Any) -> List[str]:
    """Extract all content from a LangGraph chunk (handles tuples, dicts, lists)."""
    contents = []
    
    # Handle tuple format: (stream_mode, chunk_data)
    if isinstance(chunk, tuple) and len(chunk) == 2:
        mode, data = chunk
        contents.extend(extract_content_from_chunk(data))
        return contents
    
    # Handle dict formats
    if isinstance(chunk, dict):
        # "messages" mode
        if "messages" in chunk:
            msgs = chunk["messages"]
            if isinstance(msgs, list):
                for msg in msgs:
                    content = safe_message_content(msg)
                    if content.strip():
                        contents.append(content)
        
        # "updates" mode: {"node_name": {"messages": [...]}}
        else:
            for node_name, updates in chunk.items():
                if isinstance(updates, dict) and "messages" in updates:
                    for msg in updates["messages"]:
                        content = safe_message_content(msg)
                        if content.strip():
                            contents.append(f"[{node_name}] {content}")
                elif isinstance(updates, list):
                    for msg in updates:
                        content = safe_message_content(msg)
                        if content.strip():
                            contents.append(content)
    
    # Handle single message/list
    elif isinstance(chunk, list):
        for item in chunk:
            contents.extend(extract_content_from_chunk(item))
    
    elif isinstance(chunk, (str, dict)):
        content = safe_message_content(chunk)
        if content.strip():
            contents.append(content)
    
    return contents

def extract_sql_from_content(content: str) -> str:
    """Extract SQL from response."""
    if "```sql" in content:
        start = content.find("```sql") + 6
        end = content.find("```", start)
        if end > start > 5:
            return content[start:end].strip()
    return None