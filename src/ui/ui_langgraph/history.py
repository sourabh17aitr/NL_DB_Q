"""
History display for LangGraph agent workflow UI.
"""
import streamlit as st
from config.prompt import QUERY_EXAMPLES

def render_footer():
    """Render footer with metrics and examples."""
    st.divider()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    query_history = st.session_state.get('query_history', [])
    successful_queries = sum(1 for q in query_history if q.get('success', True))
    total_retries = sum(q.get('retry_count', 0) for q in query_history)
    
    col1.metric("Total Queries", len(query_history))
    col2.metric("Successful", successful_queries)
    col3.metric("Total Retries", total_retries)
    
    # Example queries
    with st.expander("💡 Example Questions", expanded=False):
        st.markdown(QUERY_EXAMPLES)
    # Footer info
    st.caption("🔧 Powered by LangGraph workflow | 🤖 Natural Language to SQL Agent")
