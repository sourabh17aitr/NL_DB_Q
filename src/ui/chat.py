# Chat history display + input handling + streaming
import streamlit as st
from datetime import datetime
from typing import List
from .utils import extract_content_from_chunk, extract_sql_from_content
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
                full_response = ""
                
                # Init chunk counter in session state
                if 'chunk_count' not in st.session_state:
                    st.session_state.chunk_count = 0
                
                with st.spinner("🤔 Agent working..."):
                    try:
                        chunk_count = 0
                        chunks_processed = []  # Debug: collect all chunks
                        
                        # CRITICAL: Pass config with thread_id for LangGraph persistence
                        for chunk in stream_agent(agent, prompt, config):
                            chunk_count += 1
                            st.session_state.chunk_count = chunk_count  # Persist for metrics
                            
                            # Debug: Store raw chunks
                            chunks_processed.append(chunk)
                            
                            # Debug output (toggle in sidebar)
                            if st.session_state.get('show_debug', False):
                                with st.expander(f"Debug Chunk #{chunk_count}"):
                                    st.json(chunk)
                            
                            # Extract ALL content from chunk (handles LangGraph formats)
                            new_contents = extract_content_from_chunk(chunk)
                            for content in new_contents:
                                full_response += content
                            
                            # Live update if new content
                            if new_contents:
                                message_placeholder.markdown(full_response + "▌")
                        
                        st.session_state.chunk_count = chunk_count  # Final count
                        
                        # FINAL: Always show complete response (even if empty)
                        final_response = full_response.strip()
                        message_placeholder.markdown(final_response or "*(No content extracted from chunks)*")
                        
                        # Log for debug
                        st.info(f"✅ Processed {chunk_count} chunks, {len(full_response)} chars")
                        
                        # Extract SQL + save history
                        sql = extract_sql_from_content(final_response)
                        st.session_state.query_history.append({
                            "question": prompt, 
                            "sql": sql, 
                            "response": final_response,
                            "timestamp": datetime.now()
                        })
                        
                        # Add assistant message to history
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                        
                    except Exception as e:
                        import traceback
                        error_msg = f"❌ Error: {str(e)}\n\n```{traceback.format_exc()}```"
                        message_placeholder.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        st.error(f"Full error: {e}")
        else:
            st.error("❌ No agent loaded. Select provider/model in sidebar first.")
        
        st.rerun()  # Refresh to update history/metrics