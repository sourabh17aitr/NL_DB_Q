# Main Streamlit app - imports all features
import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local feature imports
from ui_langchain.main_display import init_session_state, render_page_setup
from ui_langchain.config import render_sidebar
from ui_langchain.chat import render_chat_history, handle_chat_input
from ui_langchain.history import render_footer

# Init on first load
init_session_state()
render_page_setup()

# Render features in order
with st.sidebar:
    render_sidebar()

render_chat_history()
handle_chat_input()
render_footer()