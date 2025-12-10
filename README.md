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
- `src/ui/streamlit_app.py`: Streamlit chat UI with live agent steps
- `src/agents/agent_manager.py`: Builds and streams the NLDBQ agent
- `src/agents/agent_factory.py`: Factory to create agents per provider/model
- `src/config/model_options.py`: Available LLM providers and default model
- `src/config/prompt.py`: System and ReAct prompts and examples
- `src/db/db_client.py`: Database connection client
- `src/db/db_schema_wrapper.py`: Helpers to inspect DB schema
- `notebook/`: Jupyter notebooks for configuration, DB, agents, tools, comparisons
- `pyproject.toml`: Package metadata and core dependencies
- `requirement.txt`: Extra packages for notebooks and integrations

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
  ```powershell
  python main.py
  ```
  This starts Streamlit and loads `src/ui/streamlit_app.py`.

- Or directly with Streamlit:
  ```powershell
  streamlit run src/ui/streamlit_app.py
  ```

## Using the App
- Pick a provider/model in the sidebar (defaults to Ollama `llama3-groq-tool-use`).
- Ask a question like "employees in Sales" or "Top 5 sales orders".
- Watch live agent steps: thinking, tool calls, SQL detection, and results.
- The agent follows strict safety rules (no destructive SQL), fully qualifies table names, and validates queries before execution.

## Database Configuration
- Provide a working connection via your chosen driver:
  - SQL Server (ODBC): ensure an ODBC driver is installed; use `pyodbc`.
  - MySQL: `pymysql`
  - PostgreSQL: `psycopg2-binary`
- The agent uses helpers in `src/db/` to list tables and inspect schemas.

## Notebooks
- `notebook/0.0-configuration-check.ipynb`: environment checks
- `notebook/1.x-*`: DB connection and wrapper
- `notebook/2.x-*`: agents
- `notebook/3.0-*`: tools
- `notebook/4.x-*`: NLDBQ agent variants
- `notebook/5.x-*`: vector agent
- `notebook/6.x-*`: model comparisons

## Development Notes
- Packaging is configured via `pyproject.toml` with setuptools.
- Source packages are under `src/`.
- The Streamlit page config/title is set in `streamlit_app.py`.
- Prompts and provider options are in `src/config/`.

## Troubleshooting
- If Streamlit fails to start, ensure the venv is activated and dependencies installed.
- For DB errors, verify your connection string and that the driver is installed.
- If LLM calls fail, check the relevant API key in `.env`.

## License
MIT
