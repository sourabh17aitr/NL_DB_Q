"""
Streamlit UI for Production Monitoring Dashboard
"""
import streamlit as st
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ui.ui_monitoring.utils import (
    load_monitoring_data,
    get_available_metrics_files,
    format_duration,
    calculate_performance_score
)
from ui.ui_monitoring.visualizations import (
    plot_node_execution_times,
    plot_token_usage,
    plot_execution_timeline,
    plot_cost_breakdown
)

# Page configuration
st.set_page_config(
    page_title="Production Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }
    .failure-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        font-weight: bold;
    }
    .timeline-item {
        border-left: 3px solid #1f77b4;
        padding-left: 1rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">📊 Production Monitoring Dashboard</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Data source selection
    data_source = st.radio(
        "Data Source:",
        ["Live Session", "Load from File"],
        help="Select live session data or load from exported JSON file"
    )
    
    monitoring_data = None
    
    if data_source == "Load from File":
        metrics_files = get_available_metrics_files()
        
        if metrics_files:
            selected_file = st.selectbox(
                "Select Metrics File:",
                metrics_files,
                format_func=lambda x: os.path.basename(x)
            )
            
            if st.button("📂 Load Metrics", use_container_width=True):
                monitoring_data = load_monitoring_data(selected_file)
                st.success(f"Loaded: {os.path.basename(selected_file)}")
        else:
            st.info("No exported metrics files found in the workspace.")
            st.write("Export metrics from your workflow using:")
            st.code("monitor.export_metrics('metrics.json')", language="python")
    else:
        # Live session - check session state
        if 'monitoring_data' in st.session_state:
            monitoring_data = st.session_state.monitoring_data
            st.success("📡 Live session data loaded")
        else:
            st.info("No live monitoring data available. Run a query first.")
    
    st.markdown("---")
    
    # View selection
    view = st.radio(
        "Select View:",
        ["Overview", "Node Performance", "LLM Analytics", "Timeline", "Detailed Metrics"],
        key="monitoring_view"
    )
    
    st.markdown("---")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

# Main content area
if monitoring_data:
    pipeline = monitoring_data.get('pipeline', {})
    nodes = monitoring_data.get('nodes', {})
    llm = monitoring_data.get('llm', {})
    steps = monitoring_data.get('steps', [])
    
    if view == "Overview":
        st.markdown("## 📋 Pipeline Overview")
        
        # Status banner
        if pipeline.get('success'):
            st.markdown('<div class="success-badge">✅ SUCCESS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="failure-badge">❌ FAILED</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "⏱️ Total Duration",
                format_duration(pipeline.get('total_duration', 0)),
                help="Total pipeline execution time"
            )
        
        with col2:
            st.metric(
                "🔄 Total Steps",
                pipeline.get('total_steps', 0),
                help="Number of execution steps"
            )
        
        with col3:
            st.metric(
                "🔁 Retries",
                pipeline.get('retries', 0),
                delta=f"-{pipeline.get('retries', 0)} needed" if pipeline.get('retries', 0) > 0 else "None",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                "⚠️ Failures",
                pipeline.get('validation_failures', 0) + pipeline.get('execution_failures', 0),
                help="Validation + Execution failures"
            )
        
        st.markdown("---")
        
        # Performance score
        score = calculate_performance_score(monitoring_data)
        st.markdown("### 🎯 Performance Score")
        st.progress(score / 100)
        st.write(f"**{score}/100** - ", end="")
        if score >= 80:
            st.write("Excellent performance! 🌟")
        elif score >= 60:
            st.write("Good performance 👍")
        elif score >= 40:
            st.write("Needs improvement 🔧")
        else:
            st.write("Poor performance ⚠️")
        
        st.markdown("---")
        
        # Quick stats
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🤖 LLM Usage")
            if llm.get('total_tokens', 0) > 0:
                st.write(f"**Total Calls:** {llm.get('total_calls', 0)}")
                st.write(f"**Total Tokens:** {llm.get('total_tokens', 0):,}")
                st.write(f"**Prompt Tokens:** {llm.get('prompt_tokens', 0):,}")
                st.write(f"**Completion Tokens:** {llm.get('completion_tokens', 0):,}")
                st.write(f"**Estimated Cost:** ${llm.get('estimated_cost', 0):.4f}")
            else:
                st.info("Local LLM (Ollama) - No token tracking")
        
        with col2:
            st.markdown("### 📦 Node Executions")
            total_executions = sum(n.get('executions', 0) for n in nodes.values())
            total_errors = sum(n.get('errors', 0) for n in nodes.values())
            st.write(f"**Total Executions:** {total_executions}")
            st.write(f"**Total Errors:** {total_errors}")
            st.write(f"**Unique Nodes:** {len(nodes)}")
            
            # Most time-consuming node
            if nodes:
                slowest = max(nodes.items(), key=lambda x: x[1].get('total_time', 0))
                st.write(f"**Slowest Node:** {slowest[0]} ({format_duration(slowest[1]['total_time'])})")
    
    elif view == "Node Performance":
        st.markdown("## ⚙️ Node Performance Analysis")
        
        if nodes:
            # Visualization
            fig = plot_node_execution_times(nodes)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Detailed table
            st.markdown("### 📊 Detailed Node Metrics")
            
            for node_name, metrics in sorted(nodes.items(), key=lambda x: x[1].get('total_time', 0), reverse=True):
                with st.expander(f"🔧 {node_name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Executions", metrics.get('executions', 0))
                        st.metric("Errors", metrics.get('errors', 0))
                    
                    with col2:
                        st.metric("Total Time", format_duration(metrics.get('total_time', 0)))
                        st.metric("Average Time", format_duration(metrics.get('avg_time', 0)))
                    
                    with col3:
                        if metrics.get('last_execution_time'):
                            st.metric("Last Execution", format_duration(metrics['last_execution_time']))
                        
                        # Performance indicator
                        avg_time = metrics.get('avg_time', 0)
                        if avg_time < 1:
                            st.success("🟢 Fast")
                        elif avg_time < 5:
                            st.info("🟡 Normal")
                        else:
                            st.warning("🔴 Slow")
        else:
            st.info("No node execution data available.")
    
    elif view == "LLM Analytics":
        st.markdown("## 🤖 LLM Usage Analytics")
        
        if llm.get('total_calls', 0) > 0:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Calls", llm.get('total_calls', 0))
            
            with col2:
                st.metric("Total Tokens", f"{llm.get('total_tokens', 0):,}")
            
            with col3:
                avg_tokens = llm.get('total_tokens', 0) / llm.get('total_calls', 1)
                st.metric("Avg Tokens/Call", f"{avg_tokens:,.0f}")
            
            with col4:
                st.metric("Estimated Cost", f"${llm.get('estimated_cost', 0):.4f}")
            
            st.markdown("---")
            
            # Token distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Token Distribution")
                fig = plot_token_usage(llm)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 💰 Cost Breakdown")
                fig = plot_cost_breakdown(llm)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Calls per node
            if llm.get('calls_per_node'):
                st.markdown("### 📞 Calls per Node")
                calls_data = llm['calls_per_node']
                
                for node, calls in sorted(calls_data.items(), key=lambda x: x[1], reverse=True):
                    percentage = (calls / llm['total_calls']) * 100
                    st.write(f"**{node}:** {calls} calls ({percentage:.1f}%)")
                    st.progress(percentage / 100)
        else:
            st.info("🏠 Local LLM (Ollama) - Token tracking not available")
            st.write(f"**Total LLM Calls:** {llm.get('total_calls', 0)}")
            
            if llm.get('calls_per_node'):
                st.markdown("### 📞 Calls per Node")
                for node, calls in sorted(llm['calls_per_node'].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{node}:** {calls} calls")
    
    elif view == "Timeline":
        st.markdown("## ⏱️ Execution Timeline")
        
        if steps:
            # Timeline visualization
            fig = plot_execution_timeline(steps)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Detailed timeline
            st.markdown("### 📝 Step-by-Step Execution")
            
            total_time = 0
            for i, step in enumerate(steps, 1):
                total_time += step.get('duration', 0)
                
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    st.write(f"**Step {i}**")
                
                with col2:
                    st.write(f"🔧 {step.get('node', 'Unknown')}")
                
                with col3:
                    duration = step.get('duration', 0)
                    st.write(f"⏱️ {format_duration(duration)}")
                
                # Progress bar showing time relative to total
                if total_time > 0:
                    st.progress(min(1.0, duration / (total_time / len(steps))))
        else:
            st.info("No timeline data available.")
    
    elif view == "Detailed Metrics":
        st.markdown("## 📄 Detailed Metrics")
        
        # Pipeline details
        with st.expander("🔗 Pipeline Metrics", expanded=True):
            st.json(pipeline)
        
        # Node details
        with st.expander("⚙️ Node Metrics", expanded=True):
            st.json(nodes)
        
        # LLM details
        with st.expander("🤖 LLM Metrics", expanded=True):
            st.json(llm)
        
        # Steps details
        with st.expander("📋 Execution Steps", expanded=True):
            st.json(steps)
        
        # Export button
        st.markdown("---")
        if st.button("💾 Export Metrics as JSON", use_container_width=True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitoring_export_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(monitoring_data, f, indent=2)
            
            st.success(f"✅ Metrics exported to {filename}")

else:
    # No data available
    st.info("👋 Welcome to the Production Monitoring Dashboard!")
    st.markdown("""
        ### Getting Started
        
        To view monitoring data, you can:
        
        1. **Load from File**: Select a previously exported metrics JSON file from the sidebar
        2. **Live Session**: Run a query in the main application, and monitoring data will be available here
        
        ### Features
        
        - 📊 **Overview**: High-level pipeline metrics and performance score
        - ⚙️ **Node Performance**: Detailed analysis of each execution node
        - 🤖 **LLM Analytics**: Token usage, costs, and call distribution
        - ⏱️ **Timeline**: Step-by-step execution visualization
        - 📄 **Detailed Metrics**: Raw JSON data for all metrics
        
        ### Exporting Metrics
        
        From your workflow code, export metrics using:
        
        ```python
        from agent_workflow.monitoring import ProductionMonitor
        
        monitor = ProductionMonitor()
        # ... run your pipeline ...
        monitor.export_metrics('metrics.json')
        ```
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 1rem;'>
        Production Monitoring Dashboard | Real-time Pipeline Analytics 📊
    </div>
    """,
    unsafe_allow_html=True
)
