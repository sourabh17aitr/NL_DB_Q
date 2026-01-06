# Utility functions for message/chunk processing (extracted from main file)
from typing import Any, List, Dict

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

def extract_todos(chunk: Dict[str, Any]) -> str:
    """Extract & format todos from LangGraph chunk as markdown checklist."""
    todos_md = ""
    
    # Find todos in chunk (common paths)
    for key in ["todos", "__end__", "updates", "messages"]:
        if isinstance(chunk, dict) and key in chunk:
            data = chunk[key]
            if isinstance(data, dict) and "todos" in data:
                todos_list = data["todos"].get("value", data["todos"])
            elif isinstance(data, list) and any("todos" in d for d in data if isinstance(d, dict)):
                # Handle list of updates
                for item in data:
                    if isinstance(item, dict) and "todos" in item:
                        todos_list = item["todos"].get("value", item["todos"])
                        break
                else:
                    continue
            else:
                continue
            
            # PARSE YOUR FORMAT: [{"content": "...", "status": "..."}]
            if isinstance(todos_list, list):
                formatted_todos = []
                for todo in todos_list:
                    content = todo.get("content", "")
                    status = todo.get("status", "pending")
                    if status == "completed":
                        formatted_todos.append(f"✅ **{content}**")
                    else:
                        formatted_todos.append(f"⏳ **{content}**")
                
                todos_md = "\n".join(formatted_todos)
            break
    
    return todos_md.strip() if todos_md else ""