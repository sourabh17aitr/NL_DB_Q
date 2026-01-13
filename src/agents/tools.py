"""
Database Tools Manager for LangChain agents.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy import inspect

from langchain.tools import tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit

from agents.vector_retriver_tools import get_vector_tools
from db.db_client import db_client


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# System schemas to exclude (varies by DB type)
SYSTEM_SCHEMAS = {
    'mssql': ['sys', 'master', 'tempdb', 'model', 'msdb', 'INFORMATION_SCHEMA'],
    'postgres': ['pg_catalog', 'information_schema'],
    'mysql': ['mysql', 'information_schema', 'performance_schema', 'sys'],
    'oracle': ['SYS', 'SYSTEM', 'CTXSYS', 'MDSYS', 'OLAPSYS', 'WMSYS', 'XDB']
}


class DBToolManager:
    """Manages database tools for LangChain agents."""
    
    def __init__(self) -> None:
        """Initialize database tool manager."""
        self.db = db_client.get_db()
        self.db_type = db_client.db_type.lower()
        self.inspector = inspect(self.db._engine)
    
    def _get_all_tables(self) -> List[str]:
        """Internal method to get all tables using SQLAlchemy Inspector."""
        try:
            all_tables = []
            excluded_schemas = SYSTEM_SCHEMAS.get(self.db_type, [])
            
            # Get schemas if database supports them
            if hasattr(self.inspector, 'get_schema_names'):
                schemas = [s for s in self.inspector.get_schema_names() 
                          if s not in excluded_schemas]
                
                # Get tables from each schema
                for schema in schemas:
                    try:
                        tables = self.inspector.get_table_names(schema=schema)
                        all_tables.extend([f"{schema}.{table}" for table in tables])
                    except Exception as e:
                        logger.warning(f"Skipped schema '{schema}': {e}")
            else:
                # Database doesn't have schemas (e.g., SQLite)
                all_tables = self.inspector.get_table_names()
            
            logger.info(f"Found {len(all_tables)} tables")
            return sorted(all_tables)
            
        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            return []
    
    def get_tools(self, llm):
        """Get all tools for the agent."""
        
        # Get standard SQLDatabaseToolkit tools
        toolkit = SQLDatabaseToolkit(db=self.db, llm=llm)
        agent_tools = toolkit.get_tools()
        
        # Create custom tools with access to self
        @tool
        def list_all_tables() -> List[str]:
            """
            List ALL tables from ALL schemas in the database.
            Returns fully qualified table names as ['schema.table', ...].
            Database-agnostic: works with PostgreSQL, MySQL, MSSQL, Oracle, SQLite.
            """
            return self._get_all_tables()
        
        # @tool
        # def get_table_schema(table_name: str) -> str:
        #     """
        #     Get detailed schema for a specific table including columns, types, and keys.
            
        #     Args:
        #         table_name: Table name (e.g., 'schema.table' or 'table')
            
        #     Returns:
        #         String with formatted table schema information.
        #     """
        #     try:
        #         schema_info = self.db.get_table_info([table_name])
        #         logger.info(f"Retrieved schema for: {table_name}")
        #         return schema_info
        #     except Exception as e:
        #         error_msg = f"Error getting schema for '{table_name}': {e}"
        #         logger.error(error_msg)
        #         return error_msg
        
        @tool
        def get_table_schema(table_name: str) -> str:
            """
            Get detailed schema for a specific table including columns, types, and keys.
            
            Args:
                table_name: Table name (e.g., 'schema.table' or 'table')
            
            Returns:
                String with formatted table schema information.
            """
            try:
                # Parse schema and table name
                if '.' in table_name:
                    schema_name, table = table_name.split('.', 1)
                else:
                    schema_name = None
                    table = table_name
                
                # Get column information using inspector
                columns = self.inspector.get_columns(table, schema=schema_name)
                pk_constraint = self.inspector.get_pk_constraint(table, schema=schema_name)
                foreign_keys = self.inspector.get_foreign_keys(table, schema=schema_name)
                
                # Format schema information
                schema_info = f"Table: {table_name}\n\nColumns:\n"
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                    schema_info += f"  - {col['name']}: {col_type} {nullable}\n"
                
                # Add primary key info
                if pk_constraint and pk_constraint.get('constrained_columns'):
                    pk_cols = ', '.join(pk_constraint['constrained_columns'])
                    schema_info += f"\nPrimary Key: {pk_cols}\n"
                
                # Add foreign key info
                if foreign_keys:
                    schema_info += "\nForeign Keys:\n"
                    for fk in foreign_keys:
                        fk_cols = ', '.join(fk.get('constrained_columns', []))
                        ref_table = fk.get('referred_table', '')
                        ref_cols = ', '.join(fk.get('referred_columns', []))
                        schema_info += f"  - {fk_cols} -> {ref_table}({ref_cols})\n"
                
                logger.info(f"Retrieved schema for: {table_name}")
                return schema_info
                
            except Exception as e:
                error_msg = f"Error getting schema for '{table_name}': {e}"
                logger.error(error_msg)
                return error_msg
        
        @tool
        def get_database_summary() -> Dict[str, Any]:
            """
            Get high-level database overview: total tables, schemas, and sample tables.
            
            Returns:
                Dictionary with database metadata including table count and schemas
            """
            try:
                tables = self._get_all_tables()
                
                # Extract unique schemas
                schemas = sorted(set(table.split('.')[0] for table in tables if '.' in table))
                if not schemas:
                    schemas = ['default']
                
                return {
                    "database_name": db_client.database,
                    "database_type": self.db_type,
                    "total_tables": len(tables),
                    "schemas": schemas,
                    "sample_tables": tables[:10]
                }
                
            except Exception as e:
                logger.error(f"Error in database summary: {e}")
                return {"error": str(e)}
        
        # Get vector-based search tools
        vector_tools = get_vector_tools()
        
        # Return all tools
        return agent_tools + [list_all_tables, get_table_schema, get_database_summary] + vector_tools


# Singleton instance
db_tool_manager = DBToolManager()