"""
Streamlit UI for Vector Database Schema Explorer
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ui.ui_db_schema.utils import (
    get_vector_store_info,
    get_all_documents,
    search_vector_store,
    get_collection_stats
)
from ui.ui_db_schema.ui_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME

# Page configuration
st.set_page_config(
    page_title="Vector DB Schema Explorer",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 1.5rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .document-card {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metadata-tag {
        display: inline-block;
        background-color: #e1f5fe;
        color: #01579b;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🗄️ Vector DB Schema Explorer</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info(f"**Vector DB Directory:**\n`{VECTOR_DB_SCHEMA_DIR}`")
    st.info(f"**Collection Name:**\n`{VECTOR_DB_SCHEMA_NAME}`")
    
    st.markdown("---")
    st.header("📊 Navigation")
    page = st.radio(
        "Select View:",
        ["Overview", "Browse Documents", "Search", "Statistics"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Main content area
if page == "Overview":
    st.markdown('<div class="sub-header">📋 Vector Store Overview</div>', unsafe_allow_html=True)
    
    try:
        info = get_vector_store_info()
        
        if info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📦 Collections", len(info.get('collections', [])))
            
            with col2:
                total_docs = sum(c.get('document_count', 0) for c in info.get('collections', []))
                st.metric("📄 Total Documents", total_docs)
            
            with col3:
                st.metric("🗂️ Database Type", info.get('db_type', 'N/A'))
            
            st.markdown("---")
            
            # Display collections
            st.markdown('<div class="sub-header">📚 Available Collections</div>', unsafe_allow_html=True)
            
            for collection in info.get('collections', []):
                with st.expander(f"🗃️ {collection['name']}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Documents:** {collection.get('document_count', 0)}")
                        st.write(f"**Metadata Count:** {collection.get('metadata_count', 0)}")
                    
                    with col2:
                        if collection.get('sample_metadata'):
                            st.write("**Sample Metadata:**")
                            st.json(collection['sample_metadata'])
        else:
            st.warning("⚠️ No vector store found. Please build the vector store first.")
            
            with st.expander("ℹ️ How to build the vector store"):
                st.code("""
from agents.vector_store import build_schema_vector_store
build_schema_vector_store()
                """, language="python")
    
    except Exception as e:
        st.error(f"❌ Error loading vector store: {str(e)}")
        st.exception(e)

elif page == "Browse Documents":
    st.markdown('<div class="sub-header">📖 Browse All Documents</div>', unsafe_allow_html=True)
    
    try:
        documents = get_all_documents()
        
        if documents:
            st.write(f"**Total Documents:** {len(documents)}")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                search_filter = st.text_input("🔍 Filter by table name:", "")
            with col2:
                db_types = list(set(doc['metadata'].get('db_type', 'Unknown') for doc in documents))
                db_filter = st.selectbox("Filter by database type:", ["All"] + db_types)
            
            # Apply filters
            filtered_docs = documents
            if search_filter:
                filtered_docs = [d for d in filtered_docs if search_filter.lower() in d['metadata'].get('table_name', '').lower()]
            if db_filter != "All":
                filtered_docs = [d for d in filtered_docs if d['metadata'].get('db_type') == db_filter]
            
            st.write(f"**Showing {len(filtered_docs)} documents**")
            
            # Display documents
            for idx, doc in enumerate(filtered_docs):
                with st.expander(f"📄 {doc['metadata'].get('table_name', f'Document {idx+1}')}", expanded=False):
                    # Metadata tags
                    st.markdown("**Metadata:**")
                    metadata_html = ""
                    for key, value in doc['metadata'].items():
                        metadata_html += f'<span class="metadata-tag">{key}: {value}</span>'
                    st.markdown(metadata_html, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Content
                    st.markdown("**Content:**")
                    st.text_area(
                        "Document Content",
                        doc['content'],
                        height=200,
                        key=f"doc_{idx}",
                        label_visibility="collapsed"
                    )
        else:
            st.info("ℹ️ No documents found in the vector store.")
    
    except Exception as e:
        st.error(f"❌ Error loading documents: {str(e)}")
        st.exception(e)

elif page == "Search":
    st.markdown('<div class="sub-header">🔍 Search Vector Store</div>', unsafe_allow_html=True)
    
    st.write("Search for relevant database schema information using natural language queries.")
    
    # Search input
    query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., customer information, sales orders, employee data"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        k_results = st.slider("Number of results:", min_value=1, max_value=10, value=5)
    
    if st.button("🔎 Search", type="primary", use_container_width=True):
        if query:
            try:
                with st.spinner("Searching..."):
                    results = search_vector_store(query, k_results)
                
                if results:
                    st.success(f"✅ Found {len(results)} relevant results")
                    
                    for idx, result in enumerate(results):
                        similarity_score = result.get('similarity_score', 'N/A')
                        
                        with st.expander(
                            f"📊 Result {idx+1}: {result['metadata'].get('table_name', 'Unknown')} "
                            f"(Score: {similarity_score if isinstance(similarity_score, str) else f'{similarity_score:.4f}'})",
                            expanded=(idx == 0)
                        ):
                            # Metadata
                            st.markdown("**Metadata:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Table:** {result['metadata'].get('table_name', 'N/A')}")
                                st.write(f"**Database:** {result['metadata'].get('database_name', 'N/A')}")
                            with col2:
                                st.write(f"**DB Type:** {result['metadata'].get('db_type', 'N/A')}")
                                st.write(f"**Source:** {result['metadata'].get('source', 'N/A')}")
                            
                            st.markdown("---")
                            
                            # Content
                            st.markdown("**Schema Information:**")
                            st.text_area(
                                "Content",
                                result['content'],
                                height=250,
                                key=f"search_result_{idx}",
                                label_visibility="collapsed"
                            )
                else:
                    st.warning("⚠️ No results found for your query.")
            
            except Exception as e:
                st.error(f"❌ Error during search: {str(e)}")
                st.exception(e)
        else:
            st.warning("⚠️ Please enter a search query.")

elif page == "Statistics":
    st.markdown('<div class="sub-header">📊 Vector Store Statistics</div>', unsafe_allow_html=True)
    
    try:
        stats = get_collection_stats()
        
        if stats:
            # Overall statistics
            st.markdown("### 📈 Overall Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Collections", stats.get('total_collections', 0))
            with col2:
                st.metric("Total Documents", stats.get('total_documents', 0))
            with col3:
                st.metric("Total Tables", stats.get('total_tables', 0))
            with col4:
                st.metric("Database Types", stats.get('database_types', 0))
            
            st.markdown("---")
            
            # Per collection statistics
            if stats.get('collections'):
                st.markdown("### 🗃️ Collection Details")
                
                for coll_name, coll_stats in stats['collections'].items():
                    with st.expander(f"📦 {coll_name}", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Documents", coll_stats.get('document_count', 0))
                            st.write(f"**Database:** {coll_stats.get('database', 'N/A')}")
                        
                        with col2:
                            st.metric("Tables", coll_stats.get('table_count', 0))
                            st.write(f"**DB Type:** {coll_stats.get('db_type', 'N/A')}")
                        
                        # Table list
                        if coll_stats.get('tables'):
                            st.markdown("**Tables:**")
                            table_cols = st.columns(3)
                            for i, table in enumerate(coll_stats['tables']):
                                with table_cols[i % 3]:
                                    st.write(f"• {table}")
            
            st.markdown("---")
            
            # Database distribution
            if stats.get('db_type_distribution'):
                st.markdown("### 🗂️ Database Type Distribution")
                
                import pandas as pd
                df = pd.DataFrame(
                    list(stats['db_type_distribution'].items()),
                    columns=['Database Type', 'Count']
                )
                st.bar_chart(df.set_index('Database Type'))
        else:
            st.info("ℹ️ No statistics available.")
    
    except Exception as e:
        st.error(f"❌ Error loading statistics: {str(e)}")
        st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Vector DB Schema Explorer | Built with Streamlit 🎈
    </div>
    """,
    unsafe_allow_html=True
)
