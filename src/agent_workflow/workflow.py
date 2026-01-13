import logging
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import StateGraph, END

from agent_workflow.state import NL2SQLState
from agent_workflow.config import WorkflowConfig
import agent_workflow.nodes as nodes
from agent_workflow.routers import should_execute_query, should_format_or_retry
from db.db_client import db_client
from agents.tools import db_tool_manager

logger = logging.getLogger(__name__)

# Initialize monitoring if enabled
if WorkflowConfig.ENABLE_MONITORING:
    from agent_workflow.monitoring import ProductionMonitor
    monitor = ProductionMonitor()
else:
    monitor = None

# Initialize database and model
db = SQLDatabase.from_uri(db_client.get_connection_uri())
model = init_chat_model(WorkflowConfig.get_llm_key(), temperature=WorkflowConfig.LLM_TEMPERATURE)

# Initialize tools
tools = db_tool_manager.get_tools(model)
tool_lookup = {tool.name: tool for tool in tools}

# Set global variables in nodes module
nodes.monitor = monitor
nodes.model = model
nodes.tool_lookup = tool_lookup
nodes.db = db

logger.info(f"Connected to database: {db.dialect}")
logger.info(f"Using LLM: {WorkflowConfig.get_llm_key()}")
logger.info(f"Monitoring enabled: {WorkflowConfig.ENABLE_MONITORING}")


def build_workflow():
    """Build and compile the NL2SQL workflow graph."""
    workflow = StateGraph(NL2SQLState)
    
    # Add all nodes
    workflow.add_node("parallel_schema_retrieval", nodes.parallel_schema_retrieval_node)
    workflow.add_node("query_generation", nodes.query_generation_node)
    workflow.add_node("query_validation", nodes.query_validation_node)
    workflow.add_node("query_execution", nodes.query_execution_node)
    workflow.add_node("error_recovery", nodes.error_recovery_node)
    workflow.add_node("result_formatting", nodes.result_formatting_node)
    workflow.add_node("error_response", nodes.error_response_node)
    
    # Set entry point
    workflow.set_entry_point("parallel_schema_retrieval")
    
    # Add edges
    workflow.add_edge("parallel_schema_retrieval", "query_generation")
    workflow.add_edge("query_generation", "query_validation")
    
    # Conditional routing after validation
    workflow.add_conditional_edges(
        "query_validation",
        should_execute_query,
        {
            "execute": "query_execution",
            "retry": "error_recovery",
            "failed": "error_response"
        }
    )
    
    # Conditional routing after execution
    workflow.add_conditional_edges(
        "query_execution",
        should_format_or_retry,
        {
            "format": "result_formatting",
            "retry": "error_recovery",
            "failed": "error_response"
        }
    )
    
    # Error recovery goes back to validation
    workflow.add_edge("error_recovery", "query_validation")
    
    # Terminal nodes
    workflow.add_edge("result_formatting", END)
    workflow.add_edge("error_response", END)
    
    nl2sql_graph = workflow.compile()
    
    logger.info("NL2SQL workflow compiled successfully")
    logger.info("Workflow nodes: parallel_schema_retrieval → query_generation → query_validation → query_execution → result_formatting")
    
    return nl2sql_graph


# Build the workflow
nl2sql_graph = build_workflow()
