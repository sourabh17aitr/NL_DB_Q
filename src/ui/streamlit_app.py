"""Streamlit UI with Live Agent Steps."""

import sys
import os
from datetime import datetime
import streamlit as st
import logging

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)


from src.agents.agent_manager import agent_manager
from src.config.models import model_options, llm_providers, default_llm
from src.config.prompt import QUERY_EXAMPLES

from src.config.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

def safe_tool_result(result):
    """Convert ANY tool result → string"""
    if isinstance(result, list):
        if len(result) == 0: return "No results"
        elif len(result) == 1: return str(result[0])
        else: 
            preview = "\n".join(str(row)[:100] + "..." for row in result[:5])
            return f"✅ {len(result)} rows:\n{preview}"
    elif isinstance(result, dict): return str(result)
    elif result is None: return "No data"
    return str(result)

def safe_message_content(msg):
    """Extract string from ANY message format"""
    if hasattr(msg, 'content'):
        content = msg.content
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and 'text' in content[0]:
                return content[0].get('text', '')
        return str(content)
    return ""

def safe_tool_args(args):
    """Safe tool args display"""
    if not args: return {}
    safe_args = {}
    for k, v in args.items():
        if isinstance(v, list):
            safe_args[k] = ", ".join(str(x)[:50] for x in v[:3])
        else:
            safe_args[k] = str(v)[:100]
    return safe_args

def extract_sql_from_content(content):
    """Extract SQL from response"""
    content_str = safe_message_content(content) if hasattr(content, 'content') else str(content)
    if "```sql" in content_str:
        start = content_str.find("```sql") + 6
        end = content_str.find("```", start)
        if end > start > 5:
            return content_str[start:end].strip()
    return None

# ------------------ Page Config ------------------
st.set_page_config(page_title="NLDBQ", page_icon="🗄️", layout="wide")
st.title("🧠 NLDBQ - Live SQL Agent")

# ------------------ Session State ------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "query_history" not in st.session_state: st.session_state.query_history = []
if "current_agent_key" not in st.session_state: st.session_state.current_agent_key = None
if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": "conversation_1"}}
if "agent" not in st.session_state: st.session_state.agent = None
if "agent_steps" not in st.session_state: st.session_state.agent_steps = []

# ------------------ Sidebar ------------------
with st.sidebar:
    st.title("🤖 Agent Settings")
    llm_provider = st.selectbox("Provider", llm_providers, index=llm_providers.index(default_llm["provider"]))
    model_name = st.selectbox("Model", model_options[llm_provider])
    
    agent_key = f"{llm_provider}:{model_name}"
    
    if (st.session_state.current_agent_key != agent_key or 
        st.button("🔄 Reload Agent", use_container_width=True)):
        
        with st.spinner(f"Loading {llm_provider}/{model_name}..."):
            try:
                agent = agent_manager.get_agent(llm_provider, model_name)
                st.session_state.agent = agent
                st.session_state.current_agent_key = agent_key
                st.session_state.llm_provider = llm_provider
                st.session_state.model_name = model_name
                st.success(f"✅ {llm_provider}/{model_name} ready!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Agent failed: {str(e)}")
                st.session_state.agent = None
    
    st.subheader("📋 Recent Queries")
    if st.session_state.query_history:
        for query in st.session_state.query_history[-6:][::-1]:
            with st.expander(f"{query['timestamp'].strftime('%H:%M')} - {query['question'][:40]}..."):
                if query.get('sql'):
                    st.code(query['sql'], language='sql')
    else:
        st.info("💭 No queries yet")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 New Thread", use_container_width=True):
            st.session_state.config = {"configurable": {"thread_id": f"thread_{datetime.now().timestamp()}"}}
            st.session_state.messages = []
            st.rerun()

# ------------------ Chat History ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ ENHANCED INPUT + LIVE EXECUTION ------------------
if prompt := st.chat_input("💬 Ask question (e.g., 'employees in Sales')"):
    prompt = prompt.strip()
    if not prompt: st.rerun()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
    
    agent = getattr(st.session_state, 'agent', None)
    config = st.session_state.config

    with st.chat_message("assistant"):
        # Live execution panels
        thinking_panel = st.empty()
        tools_panel = st.empty()
        sql_panel = st.empty()
        results_panel = st.empty()
        
        full_response = ""
        
        with st.spinner("🤔 Agent working..."):
            if agent:
                try:
                    stream = agent_manager.stream_agent(agent, prompt, config)
                    
                    for chunk_idx, chunk in enumerate(stream):
                        st.session_state.agent_steps.append(f"Step {chunk_idx+1}")
                        
                        # 1. THINKING (reasoning)
                        if "messages" in chunk and chunk["messages"]:
                            msg = chunk["messages"][-1]
                            # Content
                            msg_content = safe_message_content(msg)
                            #logger.debug(f"Agent chunk content: {msg_content}")
                            if msg_content:
                                full_response += msg_content
                            
                            # 🆕 TOOL DETECTION
                            tool_calls = msg.tool_calls if hasattr(msg, 'tool_calls') else []
                            if tool_calls:
                                tool_call = tool_calls[0]
                                tool_name = tool_call.get('name', 'unknown')
                                args = safe_tool_args(tool_call.get('args', {}))
                                
                                step_text = f"**🔧 Step {chunk_idx+1}:** `{tool_name}`"
                                if tool_name == "execute_sql":
                                    sql = args.get('query', '')
                                    step_text += f"\n**💾 SQL:** `{sql[:100]}{'...' if len(sql) > 100 else ''}`"
                                
                                tools_panel.markdown(step_text)
                                st.session_state.agent_steps[-1] += f" ({tool_name})"
                            
                            # SQL Highlighting
                            #sql = extract_sql_from_content(full_response)
                            #if sql:
                            #    with st.expander("💾 Generated SQL", expanded=True):
                            #        st.code(sql, language="sql")
                    
                    results_panel.markdown(full_response)
                    
                    # History
                    sql_extracted = sql_panel.markdown("") if "```sql" in full_response else "Executed"
                    st.session_state.query_history.append({
                        "question": prompt, "sql": sql_extracted, "timestamp": datetime.now()
                    })                    
                except Exception as e:
                    results_panel.error(f"❌ {str(e)}")
        
        # Clear panels
        thinking_panel.empty()
        tools_panel.empty()
        sql_panel.empty()

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ------------------ Instructions ------------------
col1, col2 = st.columns(2)
col1.metric("Queries", len(st.session_state.query_history))
col2.metric("Steps", len(st.session_state.agent_steps))
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**👈 Ask a question to see live agent steps in action!**")    

with st.expander("ℹ️ Examples"):
    st.markdown(QUERY_EXAMPLES)