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
from src.config.model_options import model_options, llm_providers, default_llm
from src.config.prompt import QUERY_EXAMPLES

logger = logging.getLogger(__name__)

# ------------------ Page Config ------------------
st.set_page_config(page_title="NLDBQ", page_icon="🗄️", layout="wide")
st.title("🧠 NLDBQ - Live SQL Agent")

# ------------------ Session State ------------------
if "messages" not in st.session_state: st.session_state.messages = []
if "query_history" not in st.session_state: st.session_state.query_history = []
if "agent_steps" not in st.session_state: st.session_state.agent_steps = []
if "llm_provider" not in st.session_state: st.session_state.llm_provider = default_llm["provider"]
if "model_name" not in st.session_state: st.session_state.model_name = default_llm["model"]
if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": "conversation_1"}}
if "agent" not in st.session_state: st.session_state.agent = None

# ------------------ Sidebar ------------------
st.sidebar.title("🤖 Agent Settings")
llm_provider = st.sidebar.selectbox(
    "Provider", llm_providers,
    index=llm_providers.index(st.session_state.llm_provider)
)

model_name = st.sidebar.selectbox("Model", model_options[llm_provider])

# ------------------ Agent Loading ------------------
if (st.session_state.llm_provider != llm_provider or 
    st.session_state.model_name != model_name or 
    st.session_state.agent is None or st.sidebar.button("🔄 Reload")):
    
    with st.spinner("Loading agent..."):
        st.session_state.agent = agent_manager.get_agent(llm_provider, model_name)
        st.session_state.llm_provider = llm_provider
        st.session_state.model_name = model_name

agent = st.session_state.agent
config = st.session_state.config


# ------------------ Chat History ------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ ENHANCED INPUT + LIVE EXECUTION ------------------
if prompt := st.chat_input("💬 Ask question (e.g., 'employees in Sales')"):
    prompt = prompt.strip()
    if not prompt: st.rerun()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

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
                            if hasattr(msg, 'content') and msg.content:
                                full_response += msg.content
                                thinking_panel.markdown(f"**💭 Thinking:**\n{msg.content}")
                                st.session_state.agent_steps[-1] += " (thinking)"
                        
                        # 2. TOOL CALLS
                        if "messages" in chunk:
                            msg = chunk["messages"][-1]
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                tool_call = msg.tool_calls[0]
                                tool_name = tool_call['name']
                                args = tool_call['args']
                                
                                tool_display = f"🛠️ **{tool_name}**"
                                if tool_name == "get_table_schema":
                                    tool_display += f"\n📋 Tables: {args.get('table_names', 'checking...')}"
                                elif tool_name == "execute_sql":
                                    tool_display += f"\n📝 SQL: {args.get('query', '')[:100]}..."
                                
                                tools_panel.markdown(tool_display)
                                st.session_state.agent_steps[-1] += f" ({tool_name})"
                        
                        # 3. SQL DETECTION
                        if "```sql" in full_response:
                            start = full_response.find("```sql") + 6
                            end = full_response.find("```", start)
                            sql = full_response[start:end].strip()
                            sql_panel.code(sql, language="sql")
                            st.session_state.agent_steps[-1] += " (SQL ready)"
                    
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

# ------------------ Sidebar History ------------------
with st.sidebar:
    st.subheader("📋 Recent Queries")
    for query in st.session_state.query_history[-5:][::-1]:
        with st.expander(f"{query['timestamp'].strftime('%H:%M')} - {query['question'][:40]}..."):
            st.code(query['sql'], language='sql')
    
    if st.button("🗑️ Clear All"):
        st.session_state.messages = []
        st.session_state.agent_steps = []
        st.session_state.query_history = []
        st.session_state.config = {"configurable": {"thread_id": f"conv_{datetime.now().timestamp()}"}}
        st.rerun()

# ------------------ Status ------------------
if agent:
    st.sidebar.success(f"✅ Ready! {st.session_state.llm_provider}/{st.session_state.model_name}")
else:
    st.sidebar.warning("⚠️ Agent loading...")

# ------------------ Instructions ------------------
col1, col2 = st.columns(2)
col1.metric("Queries", len(st.session_state.query_history))
col2.metric("Steps", len(st.session_state.agent_steps))
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**👈 Ask a question to see live agent steps in action!**")    

with st.expander("ℹ️ Examples"):
    st.markdown(QUERY_EXAMPLES)