# Sidebar: agent/model selection + loading logic
import streamlit as st
from src.config.models import llm_providers, model_options, default_llm
from src.agents.agent import get_agent
from datetime import datetime 

def render_sidebar():
    """Render agent settings sidebar."""
    st.title("🤖 Agent Settings")
    
    # Model selection
    llm_provider = st.selectbox(
        "Provider", 
        llm_providers, 
        index=llm_providers.index(default_llm["provider"])
    )
    model_name = st.selectbox("Model", model_options[llm_provider])
    
    agent_key = f"{llm_provider}:{model_name}"
    
    # Load agent
    if (st.session_state.get('current_agent_key') != agent_key or 
        st.button("🔄 Reload Agent", use_container_width=True)):
        
        with st.spinner(f"Loading {llm_provider}/{model_name}..."):
            try:
                agent = get_agent(llm_provider, model_name)
                st.session_state.agent = agent
                st.session_state.current_agent_key = agent_key
                st.session_state.llm_provider = llm_provider
                st.session_state.model_name = model_name
                st.success(f"✅ {llm_provider}/{model_name} ready!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Agent failed: {str(e)}")
                st.session_state.agent = None
    
    # Debug toggle
    st.session_state.show_debug = st.checkbox("🐛 Show debug chunks")
    
    st.divider()
    render_history_panel()
    render_clear_buttons()

def render_history_panel():
    """Recent queries in sidebar."""
    st.subheader("📋 Recent Queries")
    if st.session_state.get('query_history'):
        for query in st.session_state.query_history[-6:][::-1]:
            with st.expander(f"{query['timestamp'].strftime('%H:%M')} - {query['question'][:40]}..."):
                if query.get('sql'):
                    st.code(query['sql'], language='sql')
                if query.get('response'):
                    st.markdown(query['response'])
    else:
        st.info("💭 No queries yet")

def render_clear_buttons():
    """Clear chat/thread buttons."""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 New Thread", use_container_width=True):
            timestamp = datetime.now().timestamp()
            st.session_state.config = {"configurable": {"thread_id": f"thread_{timestamp}"}}  # [!code highlight]
            st.session_state.messages = []
            st.session_state.query_history = []  # Clear history too
            st.rerun()