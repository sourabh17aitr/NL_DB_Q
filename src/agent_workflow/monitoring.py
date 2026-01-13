import time
import json
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class ProductionMonitor:
    """Comprehensive monitoring for NL2SQL pipeline."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics."""
        self.start_time = self.end_time = None
        self.node_metrics = defaultdict(lambda: {"count": 0, "time": 0.0, "errors": 0, "last": None})
        self.llm_metrics = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0, "per_node": defaultdict(int)}
        self.pipeline_metrics = {"retries": 0, "validation_failures": 0, "execution_failures": 0, "success": False, "steps": []}
    
    def start_pipeline(self):
        """Mark pipeline start."""
        self.start_time = time.time()
        logger.info(f"Pipeline started at {datetime.now().strftime('%H:%M:%S')}")
    
    def end_pipeline(self, success: bool):
        """Mark pipeline end."""
        self.end_time = time.time()
        self.pipeline_metrics["success"] = success
        status = 'Success' if success else 'Failed'
        logger.info(f"Completed in {self.end_time - self.start_time:.2f}s ({status})")
    
    def track_node_start(self, node_name: str):
        """Track node execution start."""
        return time.time()
    
    def track_node_end(self, node_name: str, start_time: float, error: bool = False):
        """Track node execution end."""
        duration = time.time() - start_time
        metrics = self.node_metrics[node_name]
        metrics["count"] += 1
        metrics["time"] += duration
        metrics["last"] = duration
        metrics["errors"] += error
        self.pipeline_metrics["steps"].append({
            "node": node_name, 
            "duration": duration, 
            "timestamp": datetime.now().isoformat()
        })
    
    def track_llm_call(self, node_name: str, prompt_tokens: int, completion_tokens: int):
        """Track LLM usage and costs."""
        self.llm_metrics["calls"] += 1
        self.llm_metrics["prompt_tokens"] += prompt_tokens
        self.llm_metrics["completion_tokens"] += completion_tokens
        self.llm_metrics["per_node"][node_name] += 1
        
        # Cost: $2.50/$10.00 per 1M tokens (prompt/completion)
        cost = (prompt_tokens / 1000 * 0.0025) + (completion_tokens / 1000 * 0.01)
        self.llm_metrics["cost"] += cost
    
    def track_retry(self):
        self.pipeline_metrics["retries"] += 1
    
    def track_validation_failure(self):
        self.pipeline_metrics["validation_failures"] += 1
    
    def track_execution_failure(self):
        self.pipeline_metrics["execution_failures"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete monitoring summary."""
        total_time = (self.end_time - self.start_time) if self.end_time else 0
        total_tokens = self.llm_metrics["prompt_tokens"] + self.llm_metrics["completion_tokens"]
        
        return {
            "pipeline": {
                "total_duration": total_time,
                "success": self.pipeline_metrics["success"],
                **{k: v for k, v in self.pipeline_metrics.items() if k not in ["success", "steps"]},
                "total_steps": len(self.pipeline_metrics["steps"])
            },
            "nodes": {
                node: {
                    "executions": m["count"],
                    "total_time": m["time"],
                    "avg_time": m["time"] / m["count"] if m["count"] > 0 else 0,
                    "errors": m["errors"],
                    "last_execution_time": m["last"]
                }
                for node, m in self.node_metrics.items()
            },
            "llm": {
                "total_calls": self.llm_metrics["calls"],
                "total_tokens": total_tokens,
                "prompt_tokens": self.llm_metrics["prompt_tokens"],
                "completion_tokens": self.llm_metrics["completion_tokens"],
                "estimated_cost": self.llm_metrics["cost"],
                "calls_per_node": dict(self.llm_metrics["per_node"])
            },
            "steps": self.pipeline_metrics["steps"]
        }
    
    def print_summary(self):
        """Print formatted monitoring summary."""
        summary = self.get_summary()
        separator = "=" * 80
        
        logger.info(f"\n{separator}")
        logger.info("PRODUCTION MONITORING SUMMARY")
        logger.info(separator)
        
        # Pipeline metrics
        p = summary['pipeline']
        logger.info("\nPIPELINE METRICS:")
        for label, value in [
            ("Total Duration", f"{p['total_duration']:.2f}s"),
            ("Status", 'Success' if p['success'] else 'Failed'),
            ("Total Steps", p['total_steps']),
            ("Retries", p['retries']),
            ("Validation Failures", p['validation_failures']),
            ("Execution Failures", p['execution_failures'])
        ]:
            logger.info(f"   {label}: {value}")
        
        # Node metrics
        logger.info("\nNODE EXECUTION METRICS:")
        for node, m in summary['nodes'].items():
            logger.info(f"   {node}: {m['executions']} exec, {m['total_time']:.3f}s total, {m['avg_time']:.3f}s avg, {m['errors']} errors")
        
        # LLM metrics
        llm = summary['llm']
        logger.info("\nLLM USAGE METRICS:")
        logger.info(f"   Total Calls: {llm['total_calls']}")
        if llm['total_tokens'] > 0:
            logger.info(f"   Total Tokens: {llm['total_tokens']:,} (Prompt: {llm['prompt_tokens']:,}, Completion: {llm['completion_tokens']:,})")
            logger.info(f"   Estimated Cost: ${llm['estimated_cost']:.4f}")
        else:
            logger.info("   Token Usage: N/A (Ollama local model)")
        
        if llm['calls_per_node']:
            logger.info(f"   Calls per Node: {', '.join(f'{n}:{c}' for n, c in llm['calls_per_node'].items())}")
        
        # Timeline
        logger.info("\nEXECUTION TIMELINE:")
        for i, step in enumerate(summary['steps'], 1):
            logger.info(f"   {i}. {step['node']}: {step['duration']:.3f}s")
        
        logger.info(separator)
    
    def export_metrics(self, filename: str):
        """Export metrics to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
        logger.info(f"Metrics exported to {filename}")


class LLMCallbackHandler(BaseCallbackHandler):
    """Callback handler to track LLM calls."""
    
    def __init__(self, monitor: ProductionMonitor, node_name: str):
        self.monitor = monitor
        self.node_name = node_name
    
    def on_llm_end(self, response, **kwargs):
        """Track LLM call end with token usage."""
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            self.monitor.track_llm_call(
                self.node_name,
                token_usage.get('prompt_tokens', 0),
                token_usage.get('completion_tokens', 0)
            )
