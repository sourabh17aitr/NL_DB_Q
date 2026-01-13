from typing import TypedDict, Annotated, Sequence, Optional
from operator import add
from langchain_core.messages import BaseMessage


class NL2SQLState(TypedDict):
    """State for NL2SQL pipeline."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_query: str
    vector_retrieved_tables: list[str]
    vector_search_results: list[dict]
    relevant_tables: list[str]
    schema_info: str
    schema_name: Optional[str]
    generated_query: str
    validation_result: str
    validation_error: Optional[str]
    query_result: Optional[str]
    execution_error: Optional[str]
    retry_count: int
    max_retries: int
    final_response: Optional[str]
