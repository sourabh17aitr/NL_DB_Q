# NLDBQ — Natural Language Database Querying

NLDBQ is a Streamlit-based prototype that lets you ask natural-language questions and get live, explainable SQL generated and executed against your database. It uses an agent that inspects schema, reasons step by step, previews/validates SQL, and streams its actions to the UI.

## Features
- Live agent with streamed reasoning and tool calls
- Schema discovery: list tables, get table columns/relations
- Safe SQL generation: preview + validation before execution
- Multiple LLM providers: OpenAI, Anthropic, Groq, Gemini, Ollama
- Simple Streamlit UI with chat history and recent queries
- Jupyter notebooks for exploration (config, DB, agents, tools)

## Repository Structure
- `main.py`: Entrypoint to launch the Streamlit app
- `src/ui/app.py`: Main Streamlit app that imports all UI features
- `src/ui/chat.py`: Chat interface with live agent step visualization
- `src/ui/config.py`: Sidebar configuration for LLM selection
- `src/ui/history.py`: Query history and footer components
- `src/ui/main_display.py`: Page setup and session state initialization
- `src/ui/utils.py`: Utility functions for UI components
- `src/agents/agent.py`: Agent creation and streaming logic
- `src/agents/tools.py`: Database tool implementations for agent
- `src/config/models.py`: Available LLM providers and model options
- `src/config/prompt.py`: System and ReAct prompts and query examples
- `src/config/db_schema.py`: Database schema definitions
- `src/db/db_client.py`: Database connection client
- `src/db/db_schema_wrapper.py`: Helpers to inspect DB schema
- `notebook/`: Jupyter notebooks for configuration, DB, agents, tools, comparisons
- `pyproject.toml`: Package metadata and core dependencies
- `requirement.txt`: Extra packages for notebooks and integrations
- `DATA_FLOW_DIAGRAM.md`: Complete data flow and architecture diagrams

## Requirements
- Python `>= 3.10`
- A database driver for your target DB (one or more of):
  - SQL Server: `pyodbc`
  - MySQL: `pymysql`
  - PostgreSQL: `psycopg2-binary`
- Optional vector/LLM tooling: `langchain`, `langgraph`, `chromadb`, etc.

## Setup
1. Create/activate a virtual environment (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   - Core project deps (from `pyproject.toml`) using pip:
     ```powershell
     pip install -e .
     ```
   - Notebook and optional packages (from `requirement.txt`):
     ```powershell
     pip install -r requirement.txt
     ```
3. Configure environment variables in `.env` (create if missing). Common values:
   - `OPENAI_API_KEY` for OpenAI
   - `ANTHROPIC_API_KEY` for Anthropic
   - `GROQ_API_KEY` for Groq
   - `GOOGLE_API_KEY` for Gemini
   - DB connection string(s), e.g. `DB_CONNECTION_STRING`

## Running the App
- Launch via the Python entrypoint:
  - Activate a virtual environment: 

   ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

  ```powershell
  python main.py
  ```
  This starts Streamlit and loads `src/ui/app.py`.

- Or (optional) directly with Streamlit:
  ```powershell
  streamlit run src/ui/app.py
  ```


## Notebooks
- `notebook/0.0-configuration-check.ipynb`: environment checks
- `notebook/1.x-*`: DB connection and wrapper
- `notebook/2.x-*`: agents
- `notebook/3.0-*`: tools
- `notebook/4.x-*`: NLDBQ agent variants
- `notebook/5.x-*`: vector agent
- `notebook/6.x-*`: model comparisons

## Documentation
- See [DATA_FLOW_DIAGRAM.md](DATA_FLOW_DIAGRAM.md) for complete architecture and data flow diagrams
- Includes component breakdowns, sequence diagrams, and error handling flows

## Development Notes
- Packaging is configured via `pyproject.toml` with setuptools.
- Source packages are under `src/` organized by layer (ui, agents, config, db).
- The Streamlit app is modular with separate files for chat, config, history, and display.
- UI components use session state for persistence across reruns.
- Agent streaming displays real-time steps using Streamlit placeholders.
- Prompts and provider options are in `src/config/`.


