# Page config + title + init session state
import streamlit as st
from datetime import datetime

def init_session_state():
    """Initialize session state on first load."""
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    if "query_history" not in st.session_state: 
        st.session_state.query_history = []
    if "current_agent_key" not in st.session_state: 
        st.session_state.current_agent_key = None
    if "config" not in st.session_state:
        st.session_state.config = {"configurable": {"thread_id": "conversation_1"}}
    if "agent" not in st.session_state: 
        st.session_state.agent = None
    if "show_debug" not in st.session_state:
        st.session_state.show_debug = False
    if "now" not in st.session_state:
        st.session_state.now = datetime.now()

def render_page_setup():
    """Page config + title."""
    st.set_page_config(page_title="NLDBQ", page_icon="📄", layout="wide")
    st.title("🤖 NLDBQ - Live SQL Agent (Fixed Streaming)")