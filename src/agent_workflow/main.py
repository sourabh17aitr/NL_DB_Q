"""
NL2SQL Agent Workflow - Main Entry Point

This module provides the main interface for executing natural language queries
against a database using LangGraph workflow.
"""

import logging
from langchain_core.messages import HumanMessage

from agent_workflow.workflow import nl2sql_graph, monitor
from agent_workflow.config import WorkflowConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def run_nl2sql_query(query: str, max_retries: int = None):
    """
    Execute a natural language query against the database.
    
    Args:
        query: Natural language question about the database
        max_retries: Maximum number of retry attempts (default: from config)
    
    Returns:
        dict: Complete state including:
            - final_response: Natural language answer
            - generated_query: SQL query that was executed
            - relevant_tables: Tables used in the query
            - query_result: Raw SQL execution result
            - retry_count: Number of retries needed
            - execution_error: Any error encountered
    
    Example:
        >>> result = run_nl2sql_query("How many customers do we have?")
        >>> print(result["final_response"])
    """
    if max_retries is None:
        max_retries = WorkflowConfig.MAX_RETRIES
    
    if monitor:
        monitor.reset()
        monitor.start_pipeline()
    
    logger.info(f"Executing query: {query}")
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "user_query": query,
        "retry_count": 0,
        "max_retries": max_retries
    }
    
    try:
        result = nl2sql_graph.invoke(initial_state)
        success = result.get("final_response") is not None
        
        if monitor:
            monitor.end_pipeline(success)
            monitor.print_summary()
            
            if WorkflowConfig.EXPORT_METRICS:
                monitor.export_metrics(WorkflowConfig.METRICS_FILE)
        
        logger.info("Query execution completed successfully" if success else "Query execution failed")
        return result
        
    except Exception as e:
        if monitor:
            monitor.end_pipeline(False)
            monitor.print_summary()
        logger.error(f"Query execution failed with exception: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    test_query = "List the top 5 customers by order count"
    result = run_nl2sql_query(test_query)
    print("\n" + "=" * 80)
    print("FINAL RESPONSE:")
    print("=" * 80)
    print(result["final_response"])
