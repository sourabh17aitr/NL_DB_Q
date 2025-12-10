# src/db/db_schema_wrapper.py
import threading
from typing import Dict, List, Optional
from contextlib import contextmanager
from langchain_community.utilities import SQLDatabase
from src.db.db_client import db_client

class DBSchemaWrapper:
    _instance: Optional['DBSchemaWrapper'] = None
    _lock = threading.Lock()
    
    SCHEMA_LIST = ["dbo", "Sales", "Person", "Production", "HumanResources", "Purchasing"]
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.dbs: Dict[str, SQLDatabase] = {}
            self._initialized = True
            self._init_databases()
        else:
            print("DBSchemaWrapper instance already initialized. Skipping re-initialization.")
            #self._init_databases()
    
    def _init_databases(self):
        """Initialize database connections once"""
        print("🔄 Initializing DB connections...")
        uri = db_client.get_connection_uri()
        self.dbs = {
            schema: SQLDatabase.from_uri(uri,schema=schema,engine_args={"pool_pre_ping": True,"pool_recycle": 3600})
            for schema in self.SCHEMA_LIST
        }
        self.default_db = list(self.dbs.values())[0]
        print("✅ DB connections initialized (pooled)")
    
    @contextmanager
    def get_db(self, schema: str = None):
        """Context manager for safe DB access"""
        db = self.dbs.get(schema, self.default_db)
        try:
            yield db
        finally:
            # Return connection to pool
            pass
    
    def get_usable_table_names(self) -> str:
        all_tables = []
        for schema, db in self.dbs.items():
            tables = db.get_usable_table_names()
            all_tables.extend([f"{schema}.{t}" for t in tables])
        return ", ".join(all_tables)
    
    def get_table_info(self, table_names: List[str]) -> str:
        result = []
        for schema, db in self.dbs.items():
            schema_tables = [t.split(".")[-1] for t in table_names if t.startswith(f"{schema}.")]
            if schema_tables:
                result.append(db.get_table_info(schema_tables))
        return "\n".join(result) if result else "No tables found"
    
    def run(self, query: str) -> str:
        return self.default_db.run(query)
    
    def close(self):
        """Close all connections"""
        for db in self.dbs.values():
            if hasattr(db, '_engine'):
                db._engine.dispose()
        print("✅ All DB connections closed")

# Global singleton
db_schema_wrapper = DBSchemaWrapper()