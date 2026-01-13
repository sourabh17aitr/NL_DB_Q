"""
Unified Streamlit Dashboard for LangChain and LangGraph UIs
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set page configuration
st.set_page_config(
    page_title="NLDBQ Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔗 LangChain", "📊 LangGraph", "🗄️ Vector DB", "📊 Monitoring"])

# Tab 1: LangChain UI
with tab1:
    try:
        from ui_langchain.main_display import init_session_state as init_lc, render_page_setup as setup_lc
        from ui_langchain.config import render_sidebar as sidebar_lc
        from ui_langchain.chat import render_chat_history as chat_history_lc, handle_chat_input as chat_input_lc
        from ui_langchain.history import render_footer as footer_lc
        
        # Initialize LangChain UI
        init_lc()
        
        # Create two columns: sidebar and main content
        col_sidebar, col_main = st.columns([1, 3])
        
        with col_sidebar:
            st.markdown("### ⚙️ Configuration")
            sidebar_lc()
        
        with col_main:
            st.markdown("### 💬 LangChain Chat")
            chat_history_lc()
            chat_input_lc()
            footer_lc()
            
    except Exception as e:
        st.error(f"Error loading LangChain UI: {str(e)}")
        st.exception(e)

# Tab 2: LangGraph UI
with tab2:
    try:
        from ui_langgraph.main_display import init_session_state as init_lg, render_page_setup as setup_lg
        from ui_langgraph.config import render_sidebar as sidebar_lg
        from ui_langgraph.chat import render_chat_history as chat_history_lg, handle_chat_input as chat_input_lg
        from ui_langgraph.history import render_footer as footer_lg
        
        # Initialize LangGraph UI
        init_lg()
        
        # Create two columns: sidebar and main content
        col_sidebar2, col_main2 = st.columns([1, 3])
        
        with col_sidebar2:
            st.markdown("### ⚙️ Configuration")
            sidebar_lg()
        
        with col_main2:
            st.markdown("### 💬 LangGraph Chat")
            chat_history_lg()
            chat_input_lg()
            footer_lg()
            
    except Exception as e:
        st.error(f"Error loading LangGraph UI: {str(e)}")
        st.exception(e)

# Tab 3: Vector DB Schema UI
with tab3:
    try:
        from ui_db_schema.utils import (
            get_vector_store_info,
            get_all_documents,
            search_vector_store,
            get_collection_stats
        )
        from ui_db_schema.ui_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME
        
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
            .sub-header {
                font-size: 1.5rem;
                font-weight: bold;
                color: #ff7f0e;
                margin-top: 1.5rem;
            }
            .metadata-tag {
                display: inline-block;
                background-color: #e1f5fe;
                color: #01579b;
                padding: 0.2rem 0.5rem;
                border-radius: 0.3rem;
                margin: 0.2rem;
                font-size: 0.85rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Create columns for sidebar and main content
        col_sidebar_vdb, col_main_vdb = st.columns([1, 3])
        
        # Sidebar for Vector DB
        with col_sidebar_vdb:
            st.markdown("### 🗄️ Vector DB Config")
            st.info(f"**Directory:**\n`{VECTOR_DB_SCHEMA_DIR}`")
            st.info(f"**Collection:**\n`{VECTOR_DB_SCHEMA_NAME}`")
            
            page = st.radio(
                "Select View:",
                ["Overview", "Browse Documents", "Search", "Statistics"],
                key="vector_db_page"
            )
            
            if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_vector_db"):
                st.cache_data.clear()
                st.rerun()
        
        # Main content area
        with col_main_vdb:
            if page == "Overview":
                st.markdown('<div class="sub-header">📋 Vector Store Overview</div>', unsafe_allow_html=True)
                
                info = get_vector_store_info()
                
                if info:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📦 Collections", len(info.get('collections', [])))
                    
                    with col2:
                        total_docs = sum(c.get('document_count', 0) for c in info.get('collections', []))
                        st.metric("📄 Total Documents", total_docs)
                    
                    with col3:
                        st.metric("🗂️ Database Type", info.get('db_type', 'N/A'))
                    
                    st.markdown("---")
                    
                    # Display collections
                    st.markdown('<div class="sub-header">📚 Available Collections</div>', unsafe_allow_html=True)
                    
                    for collection in info.get('collections', []):
                        with st.expander(f"🗃️ {collection['name']}", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Documents:** {collection.get('document_count', 0)}")
                                st.write(f"**Metadata Count:** {collection.get('metadata_count', 0)}")
                            
                            with col2:
                                if collection.get('sample_metadata'):
                                    st.write("**Sample Metadata:**")
                                    st.json(collection['sample_metadata'])
                else:
                    st.warning("⚠️ No vector store found. Please build the vector store first.")
            
            elif page == "Browse Documents":
                st.markdown('<div class="sub-header">📖 Browse All Documents</div>', unsafe_allow_html=True)
                
                documents = get_all_documents()
                
                if documents:
                    st.write(f"**Total Documents:** {len(documents)}")
                    
                    # Filter options
                    col1, col2 = st.columns(2)
                    with col1:
                        search_filter = st.text_input("🔍 Filter by table name:", "", key="browse_filter")
                    with col2:
                        db_types = list(set(doc['metadata'].get('db_type', 'Unknown') for doc in documents))
                        db_filter = st.selectbox("Filter by database type:", ["All"] + db_types, key="browse_db_filter")
                    
                    # Apply filters
                    filtered_docs = documents
                    if search_filter:
                        filtered_docs = [d for d in filtered_docs if search_filter.lower() in d['metadata'].get('table_name', '').lower()]
                    if db_filter != "All":
                        filtered_docs = [d for d in filtered_docs if d['metadata'].get('db_type') == db_filter]
                    
                    st.write(f"**Showing {len(filtered_docs)} documents**")
                    
                    # Display documents
                    for idx, doc in enumerate(filtered_docs):
                        with st.expander(f"📄 {doc['metadata'].get('table_name', f'Document {idx+1}')}", expanded=False):
                            # Metadata tags
                            st.markdown("**Metadata:**")
                            metadata_html = ""
                            for key, value in doc['metadata'].items():
                                metadata_html += f'<span class="metadata-tag">{key}: {value}</span>'
                            st.markdown(metadata_html, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Content
                            st.markdown("**Content:**")
                            st.text_area(
                                "Document Content",
                                doc['content'],
                                height=200,
                                key=f"doc_{idx}",
                                label_visibility="collapsed"
                            )
                else:
                    st.info("ℹ️ No documents found in the vector store.")
            
            elif page == "Search":
                st.markdown('<div class="sub-header">🔍 Search Vector Store</div>', unsafe_allow_html=True)
                
                st.write("Search for relevant database schema information using natural language queries.")
                
                # Search input
                query = st.text_input(
                    "Enter your search query:",
                    placeholder="e.g., customer information, sales orders, employee data",
                    key="search_query"
                )
                
                k_results = st.slider("Number of results:", min_value=1, max_value=10, value=5, key="search_k")
                
                if st.button("🔎 Search", type="primary", use_container_width=True, key="search_button"):
                    if query:
                        with st.spinner("Searching..."):
                            results = search_vector_store(query, k_results)
                        
                        if results:
                            st.success(f"✅ Found {len(results)} relevant results")
                            
                            for idx, result in enumerate(results):
                                similarity_score = result.get('similarity_score', 'N/A')
                                
                                with st.expander(
                                    f"📊 Result {idx+1}: {result['metadata'].get('table_name', 'Unknown')} "
                                    f"(Score: {similarity_score if isinstance(similarity_score, str) else f'{similarity_score:.4f}'})",
                                    expanded=(idx == 0)
                                ):
                                    # Metadata
                                    st.markdown("**Metadata:**")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**Table:** {result['metadata'].get('table_name', 'N/A')}")
                                        st.write(f"**Database:** {result['metadata'].get('database_name', 'N/A')}")
                                    with col2:
                                        st.write(f"**DB Type:** {result['metadata'].get('db_type', 'N/A')}")
                                        st.write(f"**Source:** {result['metadata'].get('source', 'N/A')}")
                                    
                                    st.markdown("---")
                                    
                                    # Content
                                    st.markdown("**Schema Information:**")
                                    st.text_area(
                                        "Content",
                                        result['content'],
                                        height=250,
                                        key=f"search_result_{idx}",
                                        label_visibility="collapsed"
                                    )
                        else:
                            st.warning("⚠️ No results found for your query.")
                    else:
                        st.warning("⚠️ Please enter a search query.")
            
            elif page == "Statistics":
                st.markdown('<div class="sub-header">📊 Vector Store Statistics</div>', unsafe_allow_html=True)
                
                stats = get_collection_stats()
                
                if stats:
                    # Overall statistics
                    st.markdown("### 📈 Overall Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Collections", stats.get('total_collections', 0))
                    with col2:
                        st.metric("Total Documents", stats.get('total_documents', 0))
                    with col3:
                        st.metric("Total Tables", stats.get('total_tables', 0))
                    with col4:
                        st.metric("Database Types", stats.get('database_types', 0))
                    
                    st.markdown("---")
                    
                    # Per collection statistics
                    if stats.get('collections'):
                        st.markdown("### 🗃️ Collection Details")
                        
                        for coll_name, coll_stats in stats['collections'].items():
                            with st.expander(f"📦 {coll_name}", expanded=True):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("Documents", coll_stats.get('document_count', 0))
                                    st.write(f"**Database:** {coll_stats.get('database', 'N/A')}")
                                
                                with col2:
                                    st.metric("Tables", coll_stats.get('table_count', 0))
                                    st.write(f"**DB Type:** {coll_stats.get('db_type', 'N/A')}")
                                
                                # Table list
                                if coll_stats.get('tables'):
                                    st.markdown("**Tables:**")
                                    table_cols = st.columns(3)
                                    for i, table in enumerate(coll_stats['tables']):
                                        with table_cols[i % 3]:
                                            st.write(f"• {table}")
                    
                    st.markdown("---")
                    
                    # Database distribution
                    if stats.get('db_type_distribution'):
                        st.markdown("### 🗂️ Database Type Distribution")
                        
                        import pandas as pd
                        df = pd.DataFrame(
                            list(stats['db_type_distribution'].items()),
                            columns=['Database Type', 'Count']
                        )
                        st.bar_chart(df.set_index('Database Type'))
                else:
                    st.info("ℹ️ No statistics available.")
            
    except Exception as e:
        st.error(f"Error loading Vector DB UI: {str(e)}")
        st.exception(e)

# Tab 4: Production Monitoring UI
with tab4:
    try:
        from ui_monitoring.utils import (
            load_monitoring_data,
            get_available_metrics_files,
            format_duration,
            calculate_performance_score
        )
        from ui_monitoring.visualizations import (
            plot_node_execution_times,
            plot_token_usage,
            plot_execution_timeline,
            plot_cost_breakdown
        )
        import json
        from datetime import datetime
        
        # Custom CSS
        st.markdown("""
            <style>
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
            </style>
        """, unsafe_allow_html=True)
        
        # Create columns for sidebar and main content
        col_sidebar_mon, col_main_mon = st.columns([1, 3])
        
        # Sidebar for Monitoring
        with col_sidebar_mon:
            st.markdown("### 📊 Monitoring Config")
            
            # Data source selection
            data_source = st.radio(
                "Data Source:",
                ["Live Session", "Load from File"],
                help="Select live session data or load from exported JSON file",
                key="monitoring_data_source"
            )
            
            monitoring_data = None
            
            if data_source == "Load from File":
                metrics_files = get_available_metrics_files()
                
                if metrics_files:
                    selected_file = st.selectbox(
                        "Select Metrics File:",
                        metrics_files,
                        format_func=lambda x: os.path.basename(x),
                        key="monitoring_file_select"
                    )
                    
                    if st.button("📂 Load Metrics", use_container_width=True, key="load_monitoring"):
                        monitoring_data = load_monitoring_data(selected_file)
                        st.session_state.loaded_monitoring_data = monitoring_data
                        st.success(f"Loaded: {os.path.basename(selected_file)}")
                    
                    if 'loaded_monitoring_data' in st.session_state:
                        monitoring_data = st.session_state.loaded_monitoring_data
                else:
                    st.info("No exported metrics files found.")
            else:
                # Live session - check session state
                if 'monitoring_data' in st.session_state:
                    monitoring_data = st.session_state.monitoring_data
                    st.success("📡 Live session data")
                else:
                    st.info("No live data. Run a query first.")
            
            st.markdown("---")
            
            # View selection
            view = st.radio(
                "Select View:",
                ["Overview", "Node Performance", "LLM Analytics", "Timeline", "Detailed Metrics"],
                key="monitoring_view"
            )
            
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_monitoring"):
                st.rerun()
        
        # Main content area
        with col_main_mon:
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
                        st.metric("⏱️ Total Duration", format_duration(pipeline.get('total_duration', 0)))
                    with col2:
                        st.metric("🔄 Total Steps", pipeline.get('total_steps', 0))
                    with col3:
                        st.metric("🔁 Retries", pipeline.get('retries', 0))
                    with col4:
                        st.metric("⚠️ Failures", pipeline.get('validation_failures', 0) + pipeline.get('execution_failures', 0))
                    
                    st.markdown("---")
                    
                    # Performance score
                    score = calculate_performance_score(monitoring_data)
                    st.markdown("### 🎯 Performance Score")
                    st.progress(score / 100)
                    st.write(f"**{score}/100**")
                    
                    st.markdown("---")
                    
                    # Quick stats
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🤖 LLM Usage")
                        if llm.get('total_tokens', 0) > 0:
                            st.write(f"**Total Calls:** {llm.get('total_calls', 0)}")
                            st.write(f"**Total Tokens:** {llm.get('total_tokens', 0):,}")
                            st.write(f"**Estimated Cost:** ${llm.get('estimated_cost', 0):.4f}")
                        else:
                            st.info("Local LLM (Ollama)")
                    
                    with col2:
                        st.markdown("### 📦 Node Executions")
                        total_executions = sum(n.get('executions', 0) for n in nodes.values())
                        total_errors = sum(n.get('errors', 0) for n in nodes.values())
                        st.write(f"**Total Executions:** {total_executions}")
                        st.write(f"**Total Errors:** {total_errors}")
                        st.write(f"**Unique Nodes:** {len(nodes)}")
                
                elif view == "Node Performance":
                    st.markdown("## ⚙️ Node Performance Analysis")
                    
                    if nodes:
                        fig = plot_node_execution_times(nodes)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("---")
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
                    else:
                        st.info("No node execution data available.")
                
                elif view == "LLM Analytics":
                    st.markdown("## 🤖 LLM Usage Analytics")
                    
                    if llm.get('total_calls', 0) > 0:
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
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 📊 Token Distribution")
                            fig = plot_token_usage(llm)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            st.markdown("### 💰 Cost Breakdown")
                            fig = plot_cost_breakdown(llm)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        if llm.get('calls_per_node'):
                            st.markdown("### 📞 Calls per Node")
                            for node, calls in sorted(llm['calls_per_node'].items(), key=lambda x: x[1], reverse=True):
                                percentage = (calls / llm['total_calls']) * 100
                                st.write(f"**{node}:** {calls} calls ({percentage:.1f}%)")
                                st.progress(percentage / 100)
                    else:
                        st.info("🏠 Local LLM (Ollama) - Token tracking not available")
                        st.write(f"**Total LLM Calls:** {llm.get('total_calls', 0)}")
                
                elif view == "Timeline":
                    st.markdown("## ⏱️ Execution Timeline")
                    
                    if steps:
                        fig = plot_execution_timeline(steps)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("---")
                        st.markdown("### 📝 Step-by-Step Execution")
                        
                        for i, step in enumerate(steps, 1):
                            col1, col2, col3 = st.columns([1, 3, 2])
                            with col1:
                                st.write(f"**Step {i}**")
                            with col2:
                                st.write(f"🔧 {step.get('node', 'Unknown')}")
                            with col3:
                                st.write(f"⏱️ {format_duration(step.get('duration', 0))}")
                    else:
                        st.info("No timeline data available.")
                
                elif view == "Detailed Metrics":
                    st.markdown("## 📄 Detailed Metrics")
                    
                    with st.expander("🔗 Pipeline Metrics", expanded=True):
                        st.json(pipeline)
                    with st.expander("⚙️ Node Metrics", expanded=True):
                        st.json(nodes)
                    with st.expander("🤖 LLM Metrics", expanded=True):
                        st.json(llm)
                    with st.expander("📋 Execution Steps", expanded=True):
                        st.json(steps)
                    
                    st.markdown("---")
                    if st.button("💾 Export Metrics as JSON", use_container_width=True, key="export_monitoring"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"monitoring_export_{timestamp}.json"
                        
                        with open(filename, 'w') as f:
                            json.dump(monitoring_data, f, indent=2)
                        
                        st.success(f"✅ Metrics exported to {filename}")
            else:
                st.info("👋 Welcome to the Production Monitoring Dashboard!")
                st.markdown("""
                    ### Getting Started
                    
                    To view monitoring data:
                    
                    1. **Load from File**: Select an exported metrics JSON file
                    2. **Live Session**: Run a query in LangChain/LangGraph tabs
                    
                    ### Features
                    
                    - 📊 **Overview**: High-level pipeline metrics and performance score
                    - ⚙️ **Node Performance**: Detailed node execution analysis
                    - 🤖 **LLM Analytics**: Token usage and costs
                    - ⏱️ **Timeline**: Step-by-step execution visualization
                    - 📄 **Detailed Metrics**: Raw JSON data
                """)
    
    except Exception as e:
        st.error(f"Error loading Monitoring UI: {str(e)}")
        st.exception(e)
