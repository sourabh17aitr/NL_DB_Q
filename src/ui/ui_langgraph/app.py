"""
Main entry point for the LangGraph agent workflow UI.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from ui_langgraph.main_display import init_session_state, render_page_setup
from ui_langgraph.config import render_sidebar
from ui_langgraph.chat import render_chat_history, handle_chat_input
from ui_langgraph.history import render_footer

# Initialize session state and page setup
init_session_state()
render_page_setup()

# Render sidebar with configuration
with st.sidebar:
    render_sidebar()

# Main chat interface
render_chat_history()
handle_chat_input()
render_footer()
