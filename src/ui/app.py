# Main Streamlit app - imports all features
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import streamlit as st

# Local feature imports
from src.ui.main_display import init_session_state, render_page_setup
from src.ui.config import render_sidebar
from src.ui.chat import render_chat_history, handle_chat_input
from src.ui.history import render_footer

# Init on first load
init_session_state()
render_page_setup()

# Render features in order
with st.sidebar:
    render_sidebar()

render_chat_history()
handle_chat_input()
render_footer()