# File: chat_ui.py - Updated handle_chat_input
import streamlit as st
from datetime import datetime
from .utils import extract_content_from_chunk, extract_sql_from_content, extract_todos
from src.agents.agent import stream_agent

def render_chat_history():
    """Display chat history."""
    for msg in st.session_state.get('messages', []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])



def handle_chat_input():
    """Handle new user prompt + streaming response."""
    if prompt := st.chat_input("💬 Ask question (e.g., 'employees in Sales')"):
        prompt = prompt.strip()
        if not prompt: 
            st.rerun()
        
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        
        # Get agent and FULL config from session state
        agent = st.session_state.get('agent')
        config = st.session_state.get('config', {"configurable": {"thread_id": "conversation_1"}})

        if agent:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                plan_placeholder = st.empty()  # New: Plan display
                full_response = ""
                current_plan = ""  # Track live plan updates
                
                # Init chunk counter in session state
                if 'chunk_count' not in st.session_state:
                    st.session_state.chunk_count = 0
                
                with st.spinner("🤔 Agent is working..."):
                    try:
                        chunk_count = 0
                        
                        for chunk in stream_agent(agent, prompt, config):
                            chunk_count += 1
                            
                            # EXTRACT PLAN FROM CHUNK (TodoListMiddleware)
                            new_plan = extract_todos(chunk)
                            if new_plan and new_plan != current_plan:
                                current_plan = new_plan
                                # Live plan update in expander
                                with plan_placeholder.container():
                                    with st.expander(f"📋 **Agent Plan** (updated {chunk_count} steps in)", expanded=True):
                                        st.markdown(current_plan)
                            
                            # Extract main content
                            new_contents = extract_content_from_chunk(chunk)
                            for content in new_contents:
                                full_response += content
                            
                            # Live response update
                            if new_contents:
                                message_placeholder.markdown(full_response + "▌")
                        
                        # FINAL DISPLAY
                        final_response = full_response.strip()
                        message_placeholder.markdown(final_response or "*(No content extracted)*")
                        
                        # Final plan if available
                        if current_plan:
                            with plan_placeholder.container():
                                with st.expander("📋 **Final Agent Plan**", expanded=False):
                                    st.markdown(current_plan)
                        
                        st.info(f"✅ Processed {chunk_count} chunks")
                        
                        # Save history (include plan if present)
                        st.session_state.query_history.append({
                            "question": prompt, 
                            "plan": current_plan,  # Save plan for history
                            #"sql": extract_sql_from_content(final_response),
                            "response": final_response,
                            "timestamp": datetime.now()
                        })
                        
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                        
                    except Exception as e:
                        import traceback
                        error_msg = f"❌ Error: {str(e)}\n\n```{traceback.format_exc()}```"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.error("❌ No agent loaded.")
        
        st.rerun()