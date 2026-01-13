"""
Main display for LangGraph agent workflow UI.
"""
import streamlit as st
from datetime import datetime

def init_session_state():
    """Initialize session state on first load."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "show_sql" not in st.session_state:
        st.session_state.show_sql = True
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False
    if "max_retries" not in st.session_state:
        st.session_state.max_retries = 3

def render_page_setup():
    """Configure page and render title."""
    st.set_page_config(
        page_title="NL2SQL LangGraph Agent",
        page_icon="🔄",
        layout="wide"
    )
    st.title("🔄 NL2SQL - LangGraph Agent Workflow")
    st.markdown("*Natural Language to SQL using LangGraph workflow with intelligent retry and validation*")
