import os
from typing import List
import logging
import re

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
import chromadb

from config.models import get_llm, get_vector_embeddings
from agents.tools import db_tool_manager
from config.vector_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME
from db.db_client import db_client

# Disable Chroma telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
# -----------------------------
# Schema → Documents
# -----------------------------
def build_schema_documents() -> List[Document]:
    """
    Builds a list of Document objects from database schema information.
    Each table gets its own document with schema details and metadata.
    """
    llm = get_llm()
    tools = db_tool_manager.get_tools(llm=llm)

    # Identify required tools
    list_tables_tool = None
    schema_tool = None
    query_tool = None

    for tool in tools:
        logger.info(f"Available tool: {tool.name}")
        if tool.name == "list_all_tables":
            list_tables_tool = tool
        elif tool.name == "get_table_schema":
            schema_tool = tool
        elif tool.name == "sql_db_query":
            query_tool = tool

    if not list_tables_tool or not schema_tool:
        raise RuntimeError("Required SQL tools are missing")

    table_names_str = list_tables_tool.invoke("")
    logger.info(f"🔍 Raw output: {repr(table_names_str)}")

    # Handle both list and string responses
    if isinstance(table_names_str, list):
        table_names = table_names_str
    else:
        cleaned = re.sub(r'^[\[\(\{\'\"]+|[\]\)\}\'\"]+$', '', table_names_str.strip())
        # Split by comma and clean each name
        table_names = [
            name.strip().strip('()[]{}\'\"') 
            for name in cleaned.split(',')
            if name.strip() and name.strip().strip('()[]{}\'\"')
        ]

    logger.info(f"✅ Found {len(table_names)} tables:")

    schema_docs: List[Document] = []
    failed_tables = []
    success_count = 0
    for table_name in table_names:
        try:
            table_info = schema_tool.invoke(table_name)

            # Fetch sample rows (best-effort) - use database-specific syntax
            sample_info = ""
            if query_tool:
                try:
                    # Get database type and use appropriate LIMIT syntax
                    db_type = db_client.db_type.lower()
                    
                    if db_type == "mssql":
                        sample_query = f"SELECT TOP 3 * FROM {table_name}"
                    elif db_type in ["oracle"]:
                        sample_query = f"SELECT * FROM {table_name} WHERE ROWNUM <= 3"
                    else:  # postgres, mysql, sqlite
                        sample_query = f"SELECT * FROM {table_name} LIMIT 3"
                    
                    sample_data = query_tool.invoke(sample_query)
                    sample_info = f"\n\nSample Data (first 3 rows):\n{sample_data}"
                except Exception as exc:
                    sample_info = f"\n\nSample data not available: {exc}"
            else:
                logger.warning("⚠️ Query tool not available; skipping sample data retrieval.")

            content = f"""
                        Table: {table_name}

                        Schema_Details:
                        {table_info}
                        {sample_info}

                        This table can be queried to answer questions about {table_name.replace('_', ' ')}.
                        """.strip()
            logger.info(f"Document Content for {table_name}:\n{content}")
            doc = Document(
                page_content=content,
                metadata={
                    "table_name": table_name,
                    "source": "database_schema",
                    "type": "table_schema",
                    "database_name": db_client.database,
                    "db_type": db_client.db_type,
                },
            )

            schema_docs.append(doc)
            success_count += 1

        except Exception as exc:
            error_msg = str(exc)[:150]
            failed_tables.append((table_name, error_msg))
            logger.error(f"✗ ERROR: {error_msg}")

    
    if failed_tables:
        logger.warning(f"\n⚠️ Failed Tables:")
        for table, error in failed_tables:
            logger.warning(f"   • {table}: {error}")
    logger.info(f"✅ Successful: {success_count}/{len(table_names)}")
    logger.info(f"❌ Failed: {len(failed_tables)}/{len(table_names)}")
    return schema_docs


# -----------------------------
# Vector Store Builder
# -----------------------------
def build_schema_vector_store() -> None:
    """
    Builds and persists a Chroma vector store for database schema documents.
    """
    if os.path.exists(VECTOR_DB_SCHEMA_DIR) and os.listdir(VECTOR_DB_SCHEMA_DIR):
        logger.info("ℹ️ Schema vector DB already exists. Skipping build.")
        return

    logger.info("🚀 Building schema vector DB...")

    schema_docs = build_schema_documents()
    logger.info(f"📚 Total schema documents: {len(schema_docs)}")

    collection_name = VECTOR_DB_SCHEMA_NAME + "_" + db_client.db_type + "_" + db_client.database
    persist_directory = VECTOR_DB_SCHEMA_DIR + "/" + collection_name
    vectorstore = Chroma.from_documents(
        documents=schema_docs,
        embedding=get_vector_embeddings(),
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    
    logger.info("✅ Schema vector DB created successfully!")
