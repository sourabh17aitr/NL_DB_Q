"""
Visualization functions for Monitoring Dashboard
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List


def plot_node_execution_times(nodes: Dict[str, Any]) -> go.Figure:
    """
    Create bar chart of node execution times.
    
    Args:
        nodes: Node metrics dictionary
    
    Returns:
        Plotly figure
    """
    node_names = list(nodes.keys())
    total_times = [nodes[n].get('total_time', 0) for n in node_names]
    avg_times = [nodes[n].get('avg_time', 0) for n in node_names]
    executions = [nodes[n].get('executions', 0) for n in node_names]
    
    fig = go.Figure()
    
    # Total time bars
    fig.add_trace(go.Bar(
        name='Total Time',
        x=node_names,
        y=total_times,
        text=[f"{t:.3f}s" for t in total_times],
        textposition='auto',
        marker_color='#1f77b4'
    ))
    
    # Average time line
    fig.add_trace(go.Scatter(
        name='Avg Time',
        x=node_names,
        y=avg_times,
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#ff7f0e', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Node Execution Times',
        xaxis_title='Node',
        yaxis_title='Total Time (seconds)',
        yaxis2=dict(
            title='Average Time (seconds)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_token_usage(llm: Dict[str, Any]) -> go.Figure:
    """
    Create pie chart of token usage distribution.
    
    Args:
        llm: LLM metrics dictionary
    
    Returns:
        Plotly figure
    """
    prompt_tokens = llm.get('prompt_tokens', 0)
    completion_tokens = llm.get('completion_tokens', 0)
    
    fig = go.Figure(data=[go.Pie(
        labels=['Prompt Tokens', 'Completion Tokens'],
        values=[prompt_tokens, completion_tokens],
        hole=0.3,
        marker_colors=['#1f77b4', '#ff7f0e']
    )])
    
    fig.update_layout(
        title='Token Distribution',
        height=350
    )
    
    return fig


def plot_cost_breakdown(llm: Dict[str, Any]) -> go.Figure:
    """
    Create bar chart showing cost breakdown.
    
    Args:
        llm: LLM metrics dictionary
    
    Returns:
        Plotly figure
    """
    prompt_tokens = llm.get('prompt_tokens', 0)
    completion_tokens = llm.get('completion_tokens', 0)
    
    # Calculate costs (using same rates as monitoring.py)
    prompt_cost = (prompt_tokens / 1000) * 0.0025
    completion_cost = (completion_tokens / 1000) * 0.01
    
    fig = go.Figure(data=[
        go.Bar(
            name='Prompt Cost',
            x=['Cost'],
            y=[prompt_cost],
            text=f"${prompt_cost:.4f}",
            textposition='auto',
            marker_color='#1f77b4'
        ),
        go.Bar(
            name='Completion Cost',
            x=['Cost'],
            y=[completion_cost],
            text=f"${completion_cost:.4f}",
            textposition='auto',
            marker_color='#ff7f0e'
        )
    ])
    
    fig.update_layout(
        title='Cost Breakdown',
        yaxis_title='Cost (USD)',
        barmode='stack',
        height=350,
        showlegend=True
    )
    
    return fig


def plot_execution_timeline(steps: List[Dict[str, Any]]) -> go.Figure:
    """
    Create timeline visualization of execution steps.
    
    Args:
        steps: List of execution steps
    
    Returns:
        Plotly figure
    """
    step_numbers = list(range(1, len(steps) + 1))
    durations = [step.get('duration', 0) for step in steps]
    node_names = [step.get('node', 'Unknown') for step in steps]
    
    # Create color map for different nodes
    unique_nodes = list(set(node_names))
    colors = px.colors.qualitative.Plotly[:len(unique_nodes)]
    color_map = dict(zip(unique_nodes, colors))
    bar_colors = [color_map[node] for node in node_names]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=step_numbers,
        y=durations,
        text=[f"{node}<br>{dur:.3f}s" for node, dur in zip(node_names, durations)],
        textposition='auto',
        marker_color=bar_colors,
        hovertemplate='<b>Step %{x}</b><br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Execution Timeline',
        xaxis_title='Step Number',
        yaxis_title='Duration (seconds)',
        height=400,
        showlegend=False
    )
    
    return fig


def plot_error_rate(nodes: Dict[str, Any]) -> go.Figure:
    """
    Create visualization of error rates per node.
    
    Args:
        nodes: Node metrics dictionary
    
    Returns:
        Plotly figure
    """
    node_names = list(nodes.keys())
    error_rates = []
    
    for node in node_names:
        executions = nodes[node].get('executions', 0)
        errors = nodes[node].get('errors', 0)
        rate = (errors / executions * 100) if executions > 0 else 0
        error_rates.append(rate)
    
    fig = go.Figure(data=[
        go.Bar(
            x=node_names,
            y=error_rates,
            text=[f"{rate:.1f}%" for rate in error_rates],
            textposition='auto',
            marker_color=['#d62728' if rate > 10 else '#2ca02c' for rate in error_rates]
        )
    ])
    
    fig.update_layout(
        title='Error Rate by Node',
        xaxis_title='Node',
        yaxis_title='Error Rate (%)',
        height=400
    )
    
    return fig


def plot_calls_per_node(llm_calls: Dict[str, int]) -> go.Figure:
    """
    Create bar chart of LLM calls per node.
    
    Args:
        llm_calls: Dictionary of node names to call counts
    
    Returns:
        Plotly figure
    """
    nodes = list(llm_calls.keys())
    calls = list(llm_calls.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=nodes,
            y=calls,
            text=calls,
            textposition='auto',
            marker_color='#9467bd'
        )
    ])
    
    fig.update_layout(
        title='LLM Calls per Node',
        xaxis_title='Node',
        yaxis_title='Number of Calls',
        height=350
    )
    
    return fig
