from langchain_community.vectorstores import Chroma
from langchain.tools import tool
from typing import List

from db.db_client import db_client
from config.models import get_vector_embeddings
from config.vector_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME


def load_schema_vector_store():
    collection_name = VECTOR_DB_SCHEMA_NAME + "_" + db_client.db_type + "_" + db_client.database
    persist_directory = VECTOR_DB_SCHEMA_DIR + "/" + collection_name

    return Chroma(
        persist_directory=persist_directory,
        embedding_function=get_vector_embeddings(),
        collection_name=collection_name
    )

def retrieve_schema(query: str, k: int = 5):
    vectorstore = load_schema_vector_store()

    results = vectorstore.similarity_search(
        query=query,
        k=k
    )
    print(f"Vector retrieve_schema results: {results}")
    return results


# ============================================
# Tool Wrapper for Agent
# ============================================

@tool
def find_relevant_tables(question: str) -> str:
    """
    Search for relevant database tables based on a natural language question.
    Use this tool FIRST when you need to find which tables contain information 
    related to the user's query. Returns table names, schemas, and sample data.
    
    Args:
        question: Natural language description of what data you need 
                 (e.g., "employee information", "sales orders", "customer purchases")
    
    Returns:
        Formatted string with relevant table information including:
        - Table names
        - Column details
        - Sample data
    """
    try:
        print(f"Searching schema vector store for question: {question}")
        # Retrieve top 3-5 most relevant schema documents
        results = retrieve_schema(query=question, k=3)
        
        if not results:
            return "No relevant tables found. Use list_all_tables() to see all available tables."
        
        # Format results for agent consumption
        formatted_output = []
        for idx, doc in enumerate(results, 1):
            table_name = doc.metadata.get("table_name", "Unknown")
            content = doc.page_content
            formatted_output.append(f"--- Relevant Table {idx}: {table_name} ---\n{content}\n")
        print(f"Vector retrieve_schema formatted_output: {formatted_output}")
        return "\n".join(formatted_output)
    
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"


@tool
def search_tables_by_keyword(keyword: str) -> str:
    """
    Search for tables whose names or schemas contain specific keywords.
    Useful for finding tables when you know part of the table name.
    
    Args:
        keyword: Keyword to search for in table names and schemas
                (e.g., "employee", "order", "product", "customer")
    
    Returns:
        List of matching tables with their schemas
    """
    try:
        print(f"Searching schema vector store for keyword: {keyword}")
        # Retrieve more results for keyword search
        results = retrieve_schema(query=keyword, k=5)        
        
        if not results:
            return f"No tables found matching keyword: '{keyword}'"
        
        # Extract just table names for quick overview
        table_names = []
        for doc in results:
            table_name = doc.metadata.get("table_name", "Unknown")
            if table_name not in table_names:
                table_names.append(table_name)
        
        output = f"Tables matching '{keyword}':\n"
        output += "\n".join(f"  • {name}" for name in table_names)
        output += "\n\nUse get_schema() to see detailed column information for these tables."

        # Check if schema can also be capture in output

        print(f"Vector search_tables_by_keyword formatted_output: {output}")
        return output
    
    except Exception as e:
        return f"Error searching tables: {str(e)}"


# ============================================
# Integration with Tools Manager
# ============================================

def get_vector_tools() -> List:
    """
    Get list of vector store tools for agent.
    Call this from your DBToolManager to include vector-based search.
    """
    return [find_relevant_tables, search_tables_by_keyword]