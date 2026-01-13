from agent_workflow.state import NL2SQLState


def should_execute_query(state: NL2SQLState) -> str:
    """Route after validation: execute if valid, retry if failed."""
    if state.get("validation_result") == "VALID":
        return "execute"
    return "retry" if state.get("retry_count", 0) < state.get("max_retries", 3) else "failed"


def should_format_or_retry(state: NL2SQLState) -> str:
    """Route after execution: format if success, retry if error."""
    if state.get("execution_error") is None:
        return "format"
    return "retry" if state.get("retry_count", 0) < state.get("max_retries", 3) else "failed"
