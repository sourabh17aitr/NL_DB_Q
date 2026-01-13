import re
import logging
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import HumanMessage, AIMessage

from agent_workflow.state import NL2SQLState
from agent_workflow.config import WorkflowConfig
from db.db_client import db_client

logger = logging.getLogger(__name__)

# Global variables - initialized by workflow.py
monitor = None
model = None
tool_lookup = None
db = None


def parallel_schema_retrieval_node(state: NL2SQLState) -> dict:
    """
    Retrieve schemas using parallel execution of vector search and database lookup.
    Runs both operations concurrently and intelligently merges results.
    """
    node_name = "parallel_schema_retrieval"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    user_query = state["user_query"]
    logger.info("Parallel Schema Retrieval: Starting vector search & database lookup...")
    
    vector_tables = []
    vector_results = []
    db_tables = []
    schema_name = None
    
    def run_vector_search():
        """Execute vector similarity search."""
        try:
            from agents.vector_retriver_tools import retrieve_schema
            logger.info("[Vector] Searching for relevant tables...")
            results = retrieve_schema(query=user_query, k=WorkflowConfig.VECTOR_SEARCH_K)
            
            if results:
                tables = []
                info = []
                for doc in results:
                    table_name = doc.metadata.get("table_name", "Unknown")
                    if table_name not in tables:
                        tables.append(table_name)
                        info.append({
                            "table_name": table_name,
                            "content": doc.page_content,
                            "metadata": doc.metadata
                        })
                logger.info(f"[Vector] Found {len(tables)} tables: {', '.join(tables)}")
                return tables, info
            else:
                logger.warning("[Vector] No results found")
                return [], []
        except Exception as e:
            logger.warning(f"[Vector] Error: {str(e)[:80]}")
            return [], []
    
    def run_database_lookup():
        """Execute database table listing."""
        try:
            logger.info("[Database] Fetching available tables...")
            list_tables_tool = tool_lookup.get("list_all_tables")
            if not list_tables_tool:
                raise ValueError("list_all_tables tool not found")
            
            tables_result = list_tables_tool.invoke("")
            if isinstance(tables_result, list):
                tables = [t.strip() for t in tables_result]
            else:
                tables = [t.strip() for t in tables_result.split(',')]
            
            schema = next((t.split('.')[0] for t in tables if '.' in t), None)
            logger.info(f"[Database] Found {len(tables)} tables" + (f" (schema: {schema})" if schema else ""))
            return tables, schema
        except Exception as e:
            logger.warning(f"[Database] Error: {str(e)[:80]}")
            return [], None
    
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            vector_future = executor.submit(run_vector_search)
            db_future = executor.submit(run_database_lookup)
            
            vector_tables, vector_results = vector_future.result()
            db_tables, schema_name = db_future.result()
        
        logger.info("Parallel execution completed")
        
        if vector_results and vector_tables:
            logger.info(f"Using {len(vector_tables)} tables from vector search")
            schema_parts = [f"\n=== Schema for {r['table_name']} ===\n{r['content']}" 
                          for r in vector_results]
            schema_info = "\n".join(schema_parts)
            relevant_tables = vector_tables
            
            if not schema_name:
                schema_name = next((t.split('.')[0] for t in relevant_tables if '.' in t), None)
        
        elif db_tables:
            logger.warning("No vector results, using database tables with LLM filtering")
            
            all_tables_keywords = ['all tables', 'every table', 'each table', 'list tables', 
                                   'show tables', 'what tables', 'available tables']
            asks_for_all_tables = any(keyword in user_query.lower() for keyword in all_tables_keywords)
            
            if asks_for_all_tables:
                relevant_tables = db_tables
                logger.info(f"Query asks about all tables - using all {len(db_tables)} tables")
            else:
                logger.info(f"Using LLM to filter relevant tables from {len(db_tables)} available")
                prompt = f"""Given these available tables: {', '.join(db_tables)}

User question: {user_query}

Which tables are most relevant? Return ONLY comma-separated table names, no explanation."""
                
                from agent_workflow.monitoring import LLMCallbackHandler
                callback = LLMCallbackHandler(monitor, node_name) if monitor else None
                config = {"callbacks": [callback]} if callback else {}
                response = model.invoke([HumanMessage(content=prompt)], config=config)
                relevant_tables = [t.strip() for t in response.content.strip().split(',')]
                relevant_tables = [t for t in relevant_tables if t in db_tables] or db_tables
            
            schema_tool = tool_lookup.get("get_table_schema")
            if not schema_tool:
                raise ValueError("get_table_schema tool not found")
            
            schema_parts = []
            logger.info(f"Fetching schema for {len(relevant_tables)} table(s)...")
            
            for table in relevant_tables:
                try:
                    table_schema = schema_tool.invoke(table)
                    schema_parts.append(f"\n=== Schema for {table} ===\n{table_schema}")
                except Exception as e:
                    logger.warning(f"Failed to fetch schema for {table}: {str(e)[:80]}")
            
            if not schema_parts:
                raise ValueError("Could not retrieve schema for any tables")
            
            schema_info = "\n".join(schema_parts)
            logger.info(f"Retrieved schema for {len(schema_parts)} tables")
        
        else:
            raise ValueError("No tables found from either vector search or database")
        
        if schema_name:
            logger.info(f"Schema detected: {schema_name}")
        logger.info(f"Final table selection: {', '.join(relevant_tables)}")
        
        if monitor:
            monitor.track_node_end(node_name, start_time, error=False)
        
        return {
            "vector_retrieved_tables": vector_tables,
            "vector_search_results": vector_results,
            "relevant_tables": relevant_tables,
            "schema_info": schema_info,
            "schema_name": schema_name
        }
        
    except Exception as e:
        if monitor:
            monitor.track_node_end(node_name, start_time, error=True)
        raise


def query_generation_node(state: NL2SQLState) -> dict:
    """Generate SQL query from natural language."""
    node_name = "query_generation"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    try:
        user_query = state["user_query"]
        schema_info = state["schema_info"]
        schema_name = state.get("schema_name")
        
        logger.info("Query Generation: Creating SQL query...")
        
        schema_instruction = (f"\n6. Use TWO-PART table names: {schema_name}.tablename\n7. NEVER use three-part names - omit 'dbo'" 
                            if schema_name else "\n6. Use table names without schema prefix")
        if schema_name:
            logger.info(f"Using schema-qualified names: {schema_name}.tablename")
        
        prompt = f"""Given the following database schema:

{schema_info}

User question: {user_query}

Generate a SQL query to answer this question.

CRITICAL Requirements:
1. ONLY use columns that are explicitly listed in the schema above
2. ONLY use tables that are shown in the schema above
3. If customer names are needed but FirstName/LastName columns don't exist, use available ID or foreign key columns instead
4. Include appropriate LIMIT clause for large result sets (use TOP for SQL Server)
5. Use proper JOIN conditions with correct foreign key relationships from the schema
6. Return ONLY the SQL query - no explanations, comments, or markdown formatting
7. Ensure the query is syntactically correct for {db.dialect}{schema_instruction}
8. For aggregate queries across multiple tables, use UNION ALL appropriately
9. Handle NULL values properly with ISNULL() or COALESCE()
10. Use appropriate WHERE clauses to filter data efficiently

DO NOT INVENT COLUMN NAMES - if a column is not in the schema above, you CANNOT use it!

SQL Query:"""
        
        from agent_workflow.monitoring import LLMCallbackHandler
        callback = LLMCallbackHandler(monitor, node_name) if monitor else None
        config = {"callbacks": [callback]} if callback else {}
        response = model.invoke([HumanMessage(content=prompt)], config=config)
        generated_query = re.sub(r'^```sql\s*|```\s*$', '', response.content.strip(), flags=re.IGNORECASE).strip()
        
        logger.info(f"Generated SQL:\n{generated_query}")
        
        if monitor:
            monitor.track_node_end(node_name, start_time, error=False)
        
        return {"generated_query": generated_query}
    except Exception as e:
        if monitor:
            monitor.track_node_end(node_name, start_time, error=True)
        raise


def query_validation_node(state: NL2SQLState) -> dict:
    """Validate generated SQL query for safety and correctness."""
    node_name = "query_validation"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    try:
        query = state["generated_query"]
        user_query = state["user_query"]
        
        logger.info("Query Validation: Checking query safety...")
        
        # Level 1: Keyword-based safety check
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"]
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                error_msg = f"Query contains dangerous operation: {keyword}"
                logger.error(f"Validation Failed: {error_msg}")
                if monitor:
                    monitor.track_validation_failure()
                    monitor.track_node_end(node_name, start_time, error=True)
                return {
                    "validation_result": "FAILED",
                    "validation_error": error_msg
                }
        
        # Level 2: Use sql_db_query_checker tool
        try:
            query_checker_tool = tool_lookup.get("sql_db_query_checker")
            if not query_checker_tool:
                raise ValueError("sql_db_query_checker tool not found")
            
            checked_query = query_checker_tool.invoke({"query": query})
            logger.info("Query syntax validated by toolkit")
        except Exception as e:
            error_msg = f"Query checker error: {str(e)}"
            logger.error(f"Validation Failed: {error_msg}")
            if monitor:
                monitor.track_validation_failure()
                monitor.track_node_end(node_name, start_time, error=True)
            return {
                "validation_result": "FAILED",
                "validation_error": error_msg
            }
        
        # Level 3: LLM-based semantic validation
        validation_prompt = f"""Validate this SQL query for correctness and relevance:

Query: {query}

User Question: {user_query}

Validation Checklist:
1. JOIN conditions: Are all joins properly specified with correct keys?
2. Column references: Are all columns qualified with table names when needed?
3. Query relevance: Does the query actually answer the user's question?
4. Performance: Is there a LIMIT/TOP clause for potentially large result sets?
5. Logical correctness: Are aggregations, GROUP BY, and WHERE clauses correct?
6. SQL dialect: Is the syntax correct for the target database?

Respond with:
- "VALID" - if all checks pass
- "ERROR: <specific issue>" - if any check fails (be specific about the problem)"""
        
        from agent_workflow.monitoring import LLMCallbackHandler
        callback = LLMCallbackHandler(monitor, node_name) if monitor else None
        config = {"callbacks": [callback]} if callback else {}
        validation_response = model.invoke([HumanMessage(content=validation_prompt)], config=config)
        validation_result = validation_response.content.strip()
        
        validation_upper = validation_result.upper()
        is_valid = ("VALID" in validation_upper and 
                   not validation_upper.startswith("ERROR") and
                   "ERROR:" not in validation_upper)
        
        if is_valid:
            logger.info("Validation Passed: Query is valid")
            if monitor:
                monitor.track_node_end(node_name, start_time, error=False)
            return {
                "validation_result": "VALID",
                "validation_error": None
            }
        else:
            logger.error(f"Validation Failed: {validation_result}")
            if monitor:
                monitor.track_validation_failure()
                monitor.track_node_end(node_name, start_time, error=True)
            return {
                "validation_result": "FAILED",
                "validation_error": validation_result
            }
    except Exception as e:
        if monitor:
            monitor.track_node_end(node_name, start_time, error=True)
        raise


def query_execution_node(state: NL2SQLState) -> dict:
    """Execute validated SQL query."""
    node_name = "query_execution"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    try:
        query = state["generated_query"]
        
        logger.info("Query Execution: Running SQL query...")
        
        query_tool = tool_lookup.get("sql_db_query")
        if not query_tool:
            raise ValueError("sql_db_query tool not found")
        
        result = query_tool.invoke(query)
        
        logger.info("Query executed successfully")
        logger.debug(f"Result preview: {str(result)[:200]}...")
        
        if monitor:
            monitor.track_node_end(node_name, start_time, error=False)
        
        return {
            "query_result": result,
            "execution_error": None
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Execution Failed: {error_msg}")
        if monitor:
            monitor.track_execution_failure()
            monitor.track_node_end(node_name, start_time, error=True)
        
        return {
            "query_result": None,
            "execution_error": error_msg
        }


def error_recovery_node(state: NL2SQLState) -> dict:
    """Attempt to fix query errors."""
    node_name = "error_recovery"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    try:
        failed_query = state["generated_query"]
        error = state.get("execution_error") or state.get("validation_error")
        user_query = state["user_query"]
        schema_info = state["schema_info"]
        schema_name = state.get("schema_name")
        retry_count = state.get("retry_count", 0)
        
        logger.info(f"Error Recovery: Attempting to fix query (Retry {retry_count + 1})...")
        if monitor:
            monitor.track_retry()
        
        schema_note = ""
        if schema_name:
            schema_note = f"\nIMPORTANT: Use TWO-PART table names: schema.tablename (e.g., {schema_name}.Employee)\nNEVER use three-part names like {schema_name}.dbo.Employee - omit the middle 'dbo' part"
        
        recovery_prompt = f"""The following SQL query failed and needs correction:

Failed Query:
{failed_query}

Error Message:
{error}

Original User Question:
{user_query}

Database Schema:
{schema_info}{schema_note}

Common fixes to consider:
- Check column names exist in the schema
- Verify table names are correct (with schema prefix if needed, but NO middle 'dbo' part)
- Fix JOIN conditions and foreign key references
- Correct SQL syntax for {db.dialect}
- Add/fix LIMIT/TOP clause syntax
- Handle NULL values properly

Generate a corrected SQL query that fixes the error.
Return ONLY the corrected SQL query, no explanations or formatting."""
        
        from agent_workflow.monitoring import LLMCallbackHandler
        callback = LLMCallbackHandler(monitor, node_name) if monitor else None
        config = {"callbacks": [callback]} if callback else {}
        response = model.invoke([HumanMessage(content=recovery_prompt)], config=config)
        corrected_query = re.sub(r'^```sql\s*|```\s*$', '', response.content.strip(), flags=re.IGNORECASE).strip()
        
        logger.info(f"Generated corrected query:\n{corrected_query}")
        
        if monitor:
            monitor.track_node_end(node_name, start_time, error=False)
        
        return {
            "generated_query": corrected_query,
            "retry_count": retry_count + 1,
            "validation_error": None,
            "execution_error": None
        }
    except Exception as e:
        if monitor:
            monitor.track_node_end(node_name, start_time, error=True)
        raise


def result_formatting_node(state: NL2SQLState) -> dict:
    """Format SQL results into natural language response."""
    node_name = "result_formatting"
    start_time = monitor.track_node_start(node_name) if monitor else None
    
    try:
        query_result = state["query_result"]
        user_query = state["user_query"]
        generated_query = state["generated_query"]
        
        logger.info("Result Formatting: Creating natural language response...")
        
        formatting_prompt = f"""User asked: {user_query}

SQL query executed:
{generated_query}

Query returned:
{query_result}

Provide a clear, concise natural language answer to the user's question based on these results.
If the result is empty, explain that no matching data was found.
Format numbers and data in a readable way."""
        
        from agent_workflow.monitoring import LLMCallbackHandler
        callback = LLMCallbackHandler(monitor, node_name) if monitor else None
        config = {"callbacks": [callback]} if callback else {}
        response = model.invoke([HumanMessage(content=formatting_prompt)], config=config)
        final_response = response.content.strip()
        
        logger.info("Response generated")
        
        if monitor:
            monitor.track_node_end(node_name, start_time, error=False)
        
        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)]
        }
    except Exception as e:
        if monitor:
            monitor.track_node_end(node_name, start_time, error=True)
        raise


def error_response_node(state: NL2SQLState) -> dict:
    """Generate error response when max retries exceeded."""
    user_query = state["user_query"]
    error = state.get("execution_error") or state.get("validation_error", "Unknown error")
    
    error_message = f"""I apologize, but I was unable to generate a valid SQL query for your question: "{user_query}"

Error: {error}

Please try rephrasing your question or providing more specific details."""
    
    return {
        "final_response": error_message,
        "messages": [AIMessage(content=error_message)]
    }
