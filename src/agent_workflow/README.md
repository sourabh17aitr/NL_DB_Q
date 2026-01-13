# NL2SQL Agent Workflow

A production-ready Natural Language to SQL (NL2SQL) agent implementation using LangGraph. This workflow converts natural language questions into SQL queries, executes them against a database, and returns natural language responses.

## Features

- **Parallel Schema Retrieval**: Simultaneously fetches table information from vector search and database
- **Multi-Layer Validation**: Keyword-based safety checks, SQL syntax validation, and semantic validation
- **Error Recovery**: Automatic retry mechanism with intelligent query correction
- **Monitoring**: Optional comprehensive monitoring with metrics tracking
- **Configurable**: All settings configurable via environment variables
- **Database Agnostic**: Supports multiple databases (MSSQL, PostgreSQL, MySQL, Oracle)

## Architecture

### Workflow Flow

```
User Query
    ↓
Parallel Schema Retrieval (Vector Search + Database Lookup)
    ↓
Query Generation (Natural Language → SQL)
    ↓
Query Validation (Safety + Syntax + Semantic)
    ↓
Query Execution
    ↓
Result Formatting (SQL Results → Natural Language)
    ↓
Response to User
```

### File Structure

```
agent_workflow/
├── config.py          # Configuration management
├── monitoring.py      # Optional monitoring and metrics
├── state.py          # State schema definition
├── nodes.py          # Workflow node implementations
├── routers.py        # Conditional routing logic
├── workflow.py       # Workflow graph construction
├── main.py           # Main entry point
└── README.md         # This file
```

## Installation

Ensure you have the required dependencies installed:

```bash
pip install -e .
```

## Configuration

Add the following environment variables to your `.env` file:

### Required Database Configuration
```bash
# Database connection (already in your .env)
DB_TYPE=mssql
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_database
```

### LLM Configuration
```bash
# LLM Provider and Model
LLM_PROVIDER=ollama          # Options: openai, anthropic, groq, gemini, ollama
LLM_MODEL=llama3.1:8b        # Model name based on provider
LLM_TEMPERATURE=0            # Temperature for LLM responses (0-1)
```

### Workflow Configuration
```bash
# Retry settings
MAX_RETRIES=3                # Maximum retry attempts for failed queries

# Vector search settings
VECTOR_SEARCH_K=5            # Number of results to retrieve from vector search
```

### Monitoring Configuration
```bash
# Monitoring (optional)
ENABLE_MONITORING=true       # Enable/disable monitoring
EXPORT_METRICS=false         # Export metrics to JSON file
METRICS_FILE=nl2sql_metrics.json  # Metrics output file
```

## Usage

### Basic Usage

```python
from src.agent_workflow.main import run_nl2sql_query

# Execute a natural language query
result = run_nl2sql_query("How many customers do we have?")

# Access the response
print(result["final_response"])
print(result["generated_query"])
print(result["query_result"])
```

### Advanced Usage

```python
from src.agent_workflow.main import run_nl2sql_query

# Custom max retries
result = run_nl2sql_query(
    query="List the top 10 products by sales",
    max_retries=5
)

# Check for errors
if result.get("execution_error"):
    print(f"Error: {result['execution_error']}")
else:
    print(result["final_response"])
```

### Running from Command Line

```bash
# Run with default test query
python -m src.agent_workflow.main

# Or modify main.py to use your query
```

## State Schema

The workflow maintains the following state:

```python
{
    "messages": [],                    # Conversation history
    "user_query": str,                 # Original question
    "vector_retrieved_tables": [],     # Tables from vector search
    "vector_search_results": [],       # Raw vector results
    "relevant_tables": [],             # Final selected tables
    "schema_info": str,                # Table schemas
    "schema_name": str,                # Database schema name
    "generated_query": str,            # Generated SQL query
    "validation_result": str,          # "VALID" or "FAILED"
    "validation_error": str,           # Validation error message
    "query_result": str,               # SQL execution result
    "execution_error": str,            # Execution error message
    "retry_count": int,                # Current retry count
    "max_retries": int,                # Maximum retries allowed
    "final_response": str              # Natural language response
}
```

## Workflow Nodes

### 1. Parallel Schema Retrieval
- Runs vector similarity search and database table listing concurrently
- Merges results intelligently
- Retrieves table schemas for relevant tables

### 2. Query Generation
- Converts natural language to SQL
- Uses table schemas as context
- Handles schema-qualified table names
- Follows database-specific syntax rules

### 3. Query Validation
- **Level 1**: Keyword-based safety check (prevents dangerous operations)
- **Level 2**: SQL syntax validation using toolkit
- **Level 3**: Semantic validation using LLM

### 4. Query Execution
- Executes validated SQL queries
- Captures execution results or errors
- Handles database-specific nuances

### 5. Error Recovery
- Analyzes failed queries and errors
- Generates corrected SQL queries
- Supports multiple retry attempts

### 6. Result Formatting
- Converts SQL results to natural language
- Provides clear, concise answers
- Formats data for readability

### 7. Error Response
- Generates user-friendly error messages
- Provides actionable feedback

## Monitoring

When monitoring is enabled, the workflow tracks:

- **Pipeline Metrics**: Duration, success rate, retry count
- **Node Metrics**: Execution time per node, error counts
- **LLM Metrics**: Token usage, cost estimation, calls per node
- **Timeline**: Step-by-step execution timeline

### Viewing Metrics

```python
from src.agent_workflow.workflow import monitor

# Get summary
summary = monitor.get_summary()

# Print formatted summary
monitor.print_summary()

# Export to JSON
monitor.export_metrics("my_metrics.json")
```

## Examples

### Example 1: Simple Query
```python
result = run_nl2sql_query("How many employees work in each department?")
print(result["final_response"])
# Output: "There are 5 departments with the following employee counts: 
#          Sales: 25, Engineering: 40, HR: 10, Marketing: 15, Finance: 12"
```

### Example 2: Complex Query
```python
result = run_nl2sql_query(
    "Show me the top 5 customers who made the most purchases in the last 6 months"
)
print(result["generated_query"])
# Output: SELECT TOP 5 c.CustomerID, COUNT(o.OrderID) as PurchaseCount
#         FROM Sales.Customer c JOIN Sales.Orders o ON c.CustomerID = o.CustomerID
#         WHERE o.OrderDate >= DATEADD(month, -6, GETDATE())
#         GROUP BY c.CustomerID ORDER BY PurchaseCount DESC
```

### Example 3: Error Handling
```python
result = run_nl2sql_query("Show me all unicorns in the database")
if result.get("execution_error"):
    print(result["final_response"])
    # Output: "I apologize, but I was unable to find any tables related to 
    #          'unicorns' in the database. Please try a different query."
```

## Troubleshooting

### Issue: Vector search not finding tables
- Ensure vector database is properly initialized
- Check if table schemas are indexed in vector store
- Verify `VECTOR_SEARCH_K` is set appropriately

### Issue: LLM not generating valid SQL
- Check `LLM_PROVIDER` and `LLM_MODEL` are correct
- Ensure database connection is working
- Review table schemas are accessible
- Try increasing `MAX_RETRIES`

### Issue: Queries failing validation
- Check dangerous keyword filters in validation node
- Review SQL syntax for your database type
- Enable monitoring to see detailed validation errors

### Issue: Monitoring not working
- Verify `ENABLE_MONITORING=true` in `.env`
- Check that all required dependencies are installed
- Review log output for errors

## Best Practices

1. **Use descriptive queries**: "List employees in Sales department" vs "Show employees"
2. **Enable monitoring in development**: Helps identify bottlenecks
3. **Set appropriate retry limits**: Balance between success rate and performance
4. **Review generated SQL**: Check logs to understand query generation
5. **Keep vector store updated**: Regularly sync table schemas

## Performance Tips

- **Vector Search**: Adjust `VECTOR_SEARCH_K` based on database size
- **Parallel Retrieval**: Leverages concurrent execution for faster schema lookup
- **LLM Choice**: Local models (Ollama) for privacy, cloud models for accuracy
- **Monitoring Overhead**: Disable in production if not needed

## Integration

### Using in Streamlit App
```python
import streamlit as st
from src.agent_workflow.main import run_nl2sql_query

user_input = st.text_input("Ask a question about your database")
if user_input:
    result = run_nl2sql_query(user_input)
    st.write(result["final_response"])
    with st.expander("View SQL Query"):
        st.code(result["generated_query"], language="sql")
```

### Using in API
```python
from fastapi import FastAPI
from src.agent_workflow.main import run_nl2sql_query

app = FastAPI()

@app.post("/query")
async def query_database(query: str):
    result = run_nl2sql_query(query)
    return {
        "response": result["final_response"],
        "sql": result["generated_query"]
    }
```

## License

MIT

## Support

For issues and questions, please refer to the main project documentation.
