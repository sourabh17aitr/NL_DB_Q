# src/db/db_tools.py
import time
import uuid
from langchain.tools import tool
from src.db.db_schema_wrapper import DBSchemaWrapper

class DBToolManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_tools()
        return cls._instance
    
    def _log_step(self, tool_name, input_data, result):
        step = {
            "id": str(uuid.uuid4())[:6],
            "tool": tool_name,
            "input": str(input_data)[:100],
            "output": str(result)[:150] + "..." if len(str(result)) > 150 else str(result),
            "time": time.strftime("%H:%M:%S")
        }
        self.step_log.append(step)
        print(f"🔍 [{len(self.steps)}] {tool_name}({input_data[:30]}...)")
    
    def get_step_summary(self) -> str:
        """Generate human-readable step summary"""
        if not self.step_log:
            return "No steps taken yet."
        
        summary = "📋 **AGENT STEPS TAKEN:**\n\n"
        for i, step in enumerate(self.step_log, 1):
            summary += f"**Step {i}** ({step['timestamp']}): `{step['tool']}`\n"
            summary += f"   Input: {step['input'][:100]}...\n"
            summary += f"   Output: {step['result']}\n\n"
        return summary
    
    def _init_tools(self):
        self.wrapper = DBSchemaWrapper()
        self.step_log = []
        self.tools = self._create_tools()
    
    def _create_tools(self):
        @tool
        def list_all_tables() -> str:
            """List all available tables from all schemas in format schema.table_name"""
            return self.wrapper.get_usable_table_names()
        
        @tool
        def get_table_schema(table_names: str) -> str:
            """Get schema for tables. Input: 'dbo.Customers, Sales.Orders'"""
            tables = [t.strip() for t in table_names.split(",")]
            return self.wrapper.get_table_info(tables)
        
        @tool
        def preview_sql(sql: str) -> str:
            """Preview SQL query before execution."""
            return f"```sql\n{sql}\n```\n**Ready for execution**"
        
        @tool
        def execute_sql(query: str) -> str:
            """Execute approved SQL query."""
            try:
                result = self.wrapper.run(query)
                return f"✅ **Query executed successfully:**\n\n{result}"
            except Exception as e:
                return f"❌ **Execution failed:** {str(e)}"
        
        return [list_all_tables, get_table_schema, preview_sql, execute_sql]
    
    def get_tools(self):
        return self.tools[:]
    
    def get_tool_by_name(self, tool_name: str):
        """Get tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' not found")
    
    def get_step_summary(self):
        if not self.steps:
            return "No steps taken"
        
        summary = f"📋 **{len(self.steps)} STEPS TAKEN:**\n\n"
        for i, step in enumerate(self.steps, 1):
            summary += f"**{i}.** `{step['tool']}` ({step['time']})\n"
            summary += f"   📥 {step['input']}\n"
            summary += f"   📤 {step['output']}\n\n"
        return summary
    
    def clear_steps(self):
        self.step_log = []
    
    def close(self):
        self.wrapper.close()