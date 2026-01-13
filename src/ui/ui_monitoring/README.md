# Production Monitoring Dashboard

A comprehensive Streamlit dashboard for visualizing and analyzing production monitoring metrics from the NL2SQL pipeline.

## Features

- **Overview**: High-level pipeline performance metrics and scores
- **Node Performance**: Detailed analysis of execution node metrics
- **LLM Analytics**: Token usage, costs, and call distribution visualization
- **Timeline**: Step-by-step execution timeline with duration visualization
- **Detailed Metrics**: Raw JSON data export and inspection

## Installation

Ensure you have the required dependencies:

```bash
pip install streamlit plotly pandas
```

## Usage

### Running the Dashboard

From the project root:

```bash
streamlit run src/ui/ui_monitoring/app.py
```

Or from the `ui_monitoring` directory:

```bash
cd src/ui/ui_monitoring
streamlit run app.py
```

### Loading Data

The dashboard supports two data sources:

#### 1. Live Session Data

Run a query in your main application, and the monitoring data will be automatically available in the dashboard.

#### 2. Load from File

Export metrics from your workflow:

```python
from agent_workflow.monitoring import ProductionMonitor

monitor = ProductionMonitor()

# ... run your pipeline ...

# Export metrics
monitor.export_metrics('metrics.json')
```

Then load the file in the dashboard sidebar.

## Dashboard Views

### 📋 Overview
- Pipeline success/failure status
- Total duration and steps
- Retry and failure counts
- Performance score (0-100)
- Quick LLM usage statistics
- Node execution summary

### ⚙️ Node Performance
- Interactive bar chart of execution times
- Detailed metrics per node:
  - Total executions
  - Error count
  - Total and average execution time
  - Performance indicators

### 🤖 LLM Analytics
- Total calls and token usage
- Token distribution (prompt vs completion)
- Cost breakdown visualization
- Average tokens per call
- Calls per node distribution

### ⏱️ Timeline
- Visual timeline of all execution steps
- Step-by-step breakdown with durations
- Color-coded by node type
- Cumulative time tracking

### 📄 Detailed Metrics
- Raw JSON data for all metrics
- Pipeline, node, LLM, and step details
- Export functionality for further analysis

## Performance Score

The dashboard calculates a performance score (0-100) based on:

- **Success/Failure**: 50 points for successful completion
- **Retries**: -5 points per retry (max -25)
- **Failures**: -10 points per failure (max -30)
- **Speed**: Up to 20 points based on total duration
- **Efficiency**: Up to 30 points based on error rate

## File Structure

```
ui_monitoring/
├── app.py              # Main Streamlit application
├── utils.py            # Utility functions for data loading and analysis
├── visualizations.py   # Plotly visualization functions
├── __init__.py         # Module initialization
└── README.md           # This file
```

## Integration with Main Dashboard

To integrate with the main dashboard, add a new tab:

```python
# In dashboard.py
tab4 = st.tabs(["...", "📊 Monitoring"])

with tab4:
    from ui_monitoring import app as monitoring_app
    monitoring_app.main()
```

## Metrics Format

The dashboard expects JSON files with the following structure:

```json
{
  "pipeline": {
    "total_duration": 10.5,
    "success": true,
    "retries": 0,
    "validation_failures": 0,
    "execution_failures": 0,
    "total_steps": 5
  },
  "nodes": {
    "node_name": {
      "executions": 2,
      "total_time": 5.2,
      "avg_time": 2.6,
      "errors": 0,
      "last_execution_time": 2.8
    }
  },
  "llm": {
    "total_calls": 3,
    "total_tokens": 1500,
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "estimated_cost": 0.015,
    "calls_per_node": {
      "node_name": 2
    }
  },
  "steps": [
    {
      "node": "node_name",
      "duration": 2.5,
      "timestamp": "2026-01-12T10:30:00"
    }
  ]
}
```

## Troubleshooting

### No data displayed
- Ensure you've either run a query in the main app or loaded a valid metrics file
- Check that the JSON file has the correct structure

### Visualizations not appearing
- Verify plotly is installed: `pip install plotly`
- Check browser console for JavaScript errors

### Import errors
- Ensure you're running from the correct directory
- Check that parent directories are in your Python path

## Development

To extend the dashboard:

1. Add new utility functions in `utils.py`
2. Create new visualizations in `visualizations.py`
3. Add new views in `app.py`
4. Update this README with new features

## Future Enhancements

- [ ] Real-time monitoring with auto-refresh
- [ ] Comparison between multiple runs
- [ ] Historical trend analysis
- [ ] Alerting thresholds and notifications
- [ ] Export reports as PDF
- [ ] Custom metric calculations
