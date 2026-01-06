# Query history metrics + footer
import streamlit as st
from datetime import datetime
from src.config.prompt import QUERY_EXAMPLES

def render_footer():    
    """Metrics and status footer."""
    col1, col2 = st.columns(2)
    col1.metric("Queries", len(st.session_state.get('query_history', [])))
    col2.metric("Chunks Processed", st.session_state.get('chunk_count', 0)) 

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**✅ Fixed: Shows live streaming + complete final output (SQL + reasoning)**")

    with st.expander("ℹ️ Examples"):
        st.markdown(QUERY_EXAMPLES)

    st.caption("🔧 Debug mode shows raw LangGraph chunks. Toggle in sidebar.")