"""
DB Schema Wrapper - Functions accept self=None for bound method calls.
Handles type() wrapper + @tool double-binding perfectly.
"""
import logging
from typing import Dict, List
from contextlib import contextmanager
from langchain_community.utilities import SQLDatabase
from src.config.db_schema import SCHEMA_LIST
from src.db.db_client import db_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

dbs: Dict[str, SQLDatabase] = {}
_default_db = None
_initialized = False

def _init_databases():
    global dbs, _default_db, _initialized
    if _initialized: return
    
    logger.info("🔌 Initializing DB connections...")
    uri = db_client.get_connection_uri()
    
    dbs = {
        schema: SQLDatabase.from_uri(
            uri, schema=schema, 
            engine_args={"pool_pre_ping": True, "pool_recycle": 3600}
        )
        for schema in SCHEMA_LIST
    }
    _default_db = list(dbs.values())[0]
    _initialized = True
    logger.info(f"✅ {len(dbs)} schemas ready")

# ✅ FIXED: self=None catches bound method self injection
def get_usable_table_names(self=None) -> str:
    _init_databases()
    all_tables = []
    for schema, db in dbs.items():
        tables = db.get_usable_table_names()
        all_tables.extend(f"{schema}.{t}" for t in tables)
    return ", ".join(sorted(all_tables))

def get_table_info(self, table_names: List[str]) -> str:
    _init_databases()
    if not table_names:
        return "No tables specified"
    
    result = []
    for schema_name, db in dbs.items():
        schema_tables = [t.split(".")[-1] for t in table_names if t.startswith(f"{schema_name}.")]
        if schema_tables:
            try:
                info = db.get_table_info(schema_tables)
                result.append(f"Schema: {schema_name}\n{info}")
            except Exception as e:
                result.append(f"Schema: {schema_name} - Error: {e}")
    
    return "\n\n".join(result) or "No matching tables"

def run(self, query: str) -> str:
    _init_databases()
    return _default_db.run(query)

def close_all(self):
    global dbs, _default_db, _initialized
    logger.info("🔒 Closing connections...")
    for db in list(dbs.values()):
        if hasattr(db, '_engine'):
            db._engine.dispose()
    dbs.clear()
    _default_db = None
    _initialized = False

# ✅ Object with bound methods
db_schema_wrapper = type("Wrapper", (), {
    "get_usable_table_names": get_usable_table_names,
    "get_table_info": get_table_info,
    "run": run,
    "close": close_all,
})()