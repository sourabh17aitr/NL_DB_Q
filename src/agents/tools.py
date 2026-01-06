"""
DB Tools - Free functions with **kwargs for LangChain injection.
Handles config, run_manager, ToolRuntime automatically.
"""
from langchain.tools import tool
from src.db.db_schema_wrapper import db_schema_wrapper

@tool
def list_all_tables(**kwargs) -> str:  # ✅ **kwargs catches LangChain injections
    """List all available tables from all schemas in format schema.table_name"""
    return db_schema_wrapper.get_usable_table_names()

@tool
def get_table_schema(table_names: str, **kwargs) -> str:
    """Get schema for tables. Input: 'dbo.Customers, Sales.Orders'"""
    tables = [t.strip() for t in table_names.split(",")]
    return db_schema_wrapper.get_table_info(tables)

@tool
def preview_sql(sql: str, **kwargs) -> str:
    """Preview SQL query before execution."""
    return f"```sql\n{sql}\n```\n**Ready for execution**"

@tool
def execute_sql(query: str, **kwargs) -> str:
    """Execute approved SQL query."""
    try:
        result = db_schema_wrapper.run(query)
        return f"✅ **Query executed successfully:**\n\n{result}"
    except Exception as e:
        return f"❌ **Execution failed:** {str(e)}"

# Simple manager
class DBToolManager:
    def get_tools(self):
        return [list_all_tables, get_table_schema, preview_sql, execute_sql]

db_tool_manager = DBToolManager()