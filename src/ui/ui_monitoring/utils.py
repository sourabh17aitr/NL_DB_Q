"""
Utility functions for Monitoring UI
"""
import os
import json
import glob
from typing import Dict, Any, List, Optional
from pathlib import Path


def load_monitoring_data(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load monitoring data from JSON file.
    
    Args:
        filepath: Path to JSON metrics file
    
    Returns:
        Dictionary containing monitoring data or None if load fails
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading monitoring data: {e}")
        return None


def get_available_metrics_files(directory: str = ".") -> List[str]:
    """
    Get list of available metrics JSON files.
    
    Args:
        directory: Directory to search for metrics files
    
    Returns:
        List of file paths
    """
    try:
        # Search in current directory and common locations
        search_patterns = [
            os.path.join(directory, "*.json"),
            os.path.join(directory, "metrics", "*.json"),
            os.path.join(directory, "monitoring", "*.json"),
            "monitoring_export_*.json",
            "metrics_*.json"
        ]
        
        files = []
        for pattern in search_patterns:
            files.extend(glob.glob(pattern))
        
        # Filter to only files that look like monitoring data
        monitoring_files = []
        for f in files:
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    # Check if it has expected monitoring structure
                    if all(key in data for key in ['pipeline', 'nodes', 'llm']):
                        monitoring_files.append(f)
            except:
                continue
        
        return sorted(monitoring_files, key=os.path.getmtime, reverse=True)
    
    except Exception as e:
        print(f"Error finding metrics files: {e}")
        return []


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "2.45s", "1m 30s")
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def calculate_performance_score(monitoring_data: Dict[str, Any]) -> int:
    """
    Calculate overall performance score (0-100).
    
    Factors:
    - Success/Failure: 50 points
    - Retries: -5 points each
    - Failures: -10 points each
    - Speed: 20 points (based on total duration)
    - Efficiency: 30 points (based on node execution times)
    
    Args:
        monitoring_data: Monitoring data dictionary
    
    Returns:
        Performance score (0-100)
    """
    score = 0
    
    pipeline = monitoring_data.get('pipeline', {})
    nodes = monitoring_data.get('nodes', {})
    
    # Success/Failure (50 points)
    if pipeline.get('success'):
        score += 50
    
    # Retries penalty (-5 points each, max -25)
    retries = pipeline.get('retries', 0)
    score -= min(25, retries * 5)
    
    # Failures penalty (-10 points each, max -30)
    failures = pipeline.get('validation_failures', 0) + pipeline.get('execution_failures', 0)
    score -= min(30, failures * 10)
    
    # Speed score (20 points based on duration)
    duration = pipeline.get('total_duration', 0)
    if duration > 0:
        if duration < 5:
            score += 20
        elif duration < 15:
            score += 15
        elif duration < 30:
            score += 10
        elif duration < 60:
            score += 5
    
    # Efficiency score (30 points based on error rate)
    if nodes:
        total_executions = sum(n.get('executions', 0) for n in nodes.values())
        total_errors = sum(n.get('errors', 0) for n in nodes.values())
        
        if total_executions > 0:
            error_rate = total_errors / total_executions
            if error_rate == 0:
                score += 30
            elif error_rate < 0.1:
                score += 25
            elif error_rate < 0.2:
                score += 20
            elif error_rate < 0.3:
                score += 15
            elif error_rate < 0.5:
                score += 10
    
    return max(0, min(100, score))


def get_node_summary(nodes: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary statistics for nodes.
    
    Args:
        nodes: Node metrics dictionary
    
    Returns:
        Summary statistics
    """
    if not nodes:
        return {}
    
    total_executions = sum(n.get('executions', 0) for n in nodes.values())
    total_errors = sum(n.get('errors', 0) for n in nodes.values())
    total_time = sum(n.get('total_time', 0) for n in nodes.values())
    
    # Find slowest and fastest nodes
    slowest = max(nodes.items(), key=lambda x: x[1].get('avg_time', 0))
    fastest = min(nodes.items(), key=lambda x: x[1].get('avg_time', 0))
    
    return {
        'total_executions': total_executions,
        'total_errors': total_errors,
        'total_time': total_time,
        'error_rate': total_errors / total_executions if total_executions > 0 else 0,
        'slowest_node': {'name': slowest[0], 'avg_time': slowest[1].get('avg_time', 0)},
        'fastest_node': {'name': fastest[0], 'avg_time': fastest[1].get('avg_time', 0)},
        'unique_nodes': len(nodes)
    }


def get_llm_summary(llm: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary statistics for LLM usage.
    
    Args:
        llm: LLM metrics dictionary
    
    Returns:
        Summary statistics
    """
    total_calls = llm.get('total_calls', 0)
    total_tokens = llm.get('total_tokens', 0)
    
    summary = {
        'total_calls': total_calls,
        'total_tokens': total_tokens,
        'avg_tokens_per_call': total_tokens / total_calls if total_calls > 0 else 0,
        'estimated_cost': llm.get('estimated_cost', 0),
        'is_local': total_tokens == 0,  # Ollama doesn't report tokens
    }
    
    # Cost per call
    if total_calls > 0 and llm.get('estimated_cost', 0) > 0:
        summary['cost_per_call'] = llm['estimated_cost'] / total_calls
    
    return summary


def export_monitoring_summary(monitoring_data: Dict[str, Any], output_path: str):
    """
    Export a formatted summary of monitoring data.
    
    Args:
        monitoring_data: Monitoring data dictionary
        output_path: Path to save summary
    """
    try:
        summary = {
            'timestamp': monitoring_data.get('timestamp', 'N/A'),
            'performance_score': calculate_performance_score(monitoring_data),
            'pipeline': monitoring_data.get('pipeline', {}),
            'node_summary': get_node_summary(monitoring_data.get('nodes', {})),
            'llm_summary': get_llm_summary(monitoring_data.get('llm', {}))
        }
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error exporting summary: {e}")
        return False
