"""
Configuration panel for LangGraph agent workflow UI.
"""
import streamlit as st
from datetime import datetime

def render_sidebar():
    """Render sidebar with settings and controls."""
    st.title("⚙️ Workflow Settings")
    
    # Workflow settings
    st.subheader("Agent Configuration")
    st.session_state.max_retries = st.slider(
        "Max Retries",
        min_value=1,
        max_value=5,
        value=st.session_state.get('max_retries', 3),
        key="lg_max_retries",
        help="Maximum number of retry attempts for query generation and execution"
    )
    
    # Display options
    st.divider()
    st.subheader("Display Options")
    st.session_state.show_sql = st.checkbox(
        "📝 Show SQL Queries",
        value=st.session_state.get('show_sql', True),
        key="lg_show_sql",
        help="Display generated SQL queries in the chat"
    )
    st.session_state.show_debug = st.checkbox(
        "🐛 Show Debug Info",
        value=st.session_state.get('show_debug', False),
        key="lg_show_debug",
        help="Display debug information and error traces"
    )
    
    st.divider()
    render_history_panel()
    render_clear_buttons()

def render_history_panel():
    """Display recent query history in sidebar."""
    st.subheader("📋 Recent Queries")
    if st.session_state.get('query_history'):
        for idx, query in enumerate(st.session_state.query_history[-5:][::-1]):
            status_icon = "✅" if query.get('success', True) else "❌"
            timestamp = query['timestamp'].strftime('%H:%M:%S')
            
            with st.expander(f"{status_icon} {timestamp} - {query['question'][:30]}..."):
                st.markdown(f"**Question:** {query['question']}")
                if query.get('sql'):
                    st.code(query['sql'], language='sql')
                if query.get('retry_count', 0) > 0:
                    st.caption(f"🔄 Retries: {query['retry_count']}")
                st.markdown(f"**Response:** {query['response'][:200]}...")
    else:
        st.info("💭 No queries yet. Start by asking a question!")

def render_clear_buttons():
    """Render clear chat and history buttons."""
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", key="lg_clear_chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Clear History", key="lg_clear_history", use_container_width=True):
            st.session_state.query_history = []
            st.rerun()
