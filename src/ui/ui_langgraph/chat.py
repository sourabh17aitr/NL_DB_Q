"""
Chat interface for LangGraph agent workflow UI.
"""
import streamlit as st
from datetime import datetime
from agent_workflow.main import run_nl2sql_query
from ui_langgraph.utils import format_sql_query, extract_sql_from_result

def render_chat_history():
    """Display chat history with proper formatting."""
    for msg in st.session_state.get('messages', []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show SQL query if available
            if msg.get("sql") and st.session_state.show_sql:
                with st.expander("📝 Generated SQL Query", expanded=False):
                    st.code(msg["sql"], language="sql")
            
            # Show debug info if enabled
            if msg.get("debug_info") and st.session_state.show_debug:
                with st.expander("🐛 Debug Information", expanded=False):
                    st.json(msg["debug_info"])

def handle_chat_input():
    """Handle new user input and agent response."""
    if prompt := st.chat_input("💬 Ask a question about your database (e.g., 'How many customers are there?')", key="lg_chat_input"):
        prompt = prompt.strip()
        if not prompt:
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            sql_placeholder = st.empty()
            
            with st.spinner("🤔 Agent is analyzing your question..."):
                try:
                    # Call LangGraph workflow
                    max_retries = st.session_state.get('max_retries', 3)
                    result = run_nl2sql_query(prompt, max_retries=max_retries)
                    
                    # Extract information from result
                    final_response = result.get("final_response", "No response generated")
                    generated_query = result.get("generated_query", "")
                    query_result = result.get("query_result", "")
                    retry_count = result.get("retry_count", 0)
                    execution_error = result.get("execution_error")
                    
                    # Display response
                    message_placeholder.markdown(final_response)
                    
                    # Show SQL query
                    if generated_query and st.session_state.show_sql:
                        with sql_placeholder.container():
                            with st.expander("📝 Generated SQL Query", expanded=True):
                                st.code(generated_query, language="sql")
                                if retry_count > 0:
                                    st.info(f"✨ Query refined after {retry_count} attempt(s)")
                    
                    # Show success indicator
                    if not execution_error:
                        st.success(f"✅ Query executed successfully!")
                    
                    # Save to history
                    st.session_state.query_history.append({
                        "question": prompt,
                        "sql": generated_query,
                        "response": final_response,
                        "retry_count": retry_count,
                        "timestamp": datetime.now(),
                        "success": not execution_error
                    })
                    
                    # Save to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_response,
                        "sql": generated_query,
                        "debug_info": {
                            "retry_count": retry_count,
                            "execution_error": execution_error,
                            "query_result_preview": str(query_result)[:200] if query_result else None
                        }
                    })
                    
                except Exception as e:
                    import traceback
                    error_msg = f"❌ Error: {str(e)}"
                    message_placeholder.error(error_msg)
                    
                    if st.session_state.show_debug:
                        with st.expander("🐛 Full Error Trace", expanded=True):
                            st.code(traceback.format_exc())
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "debug_info": {"traceback": traceback.format_exc()}
                    })
        
        st.rerun()
