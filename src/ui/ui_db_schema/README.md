# Vector DB Schema Explorer UI

A Streamlit-based user interface for exploring and querying vector database schema collections.

## Features

- **Overview**: View all available vector store collections with statistics
- **Browse Documents**: Navigate through all stored documents with filtering capabilities
- **Search**: Perform semantic search across schema documents
- **Statistics**: View detailed statistics about collections and tables

## Installation

Ensure you have the required dependencies:

```bash
pip install streamlit chromadb langchain langchain-community
```

## Usage

### Running the UI

From the project root directory:

```bash
streamlit run src/ui/ui_db_schema/app.py
```

Or from the `ui_db_schema` directory:

```bash
cd src/ui/ui_db_schema
streamlit run app.py
```

### Building Vector Store First

Before using the UI, make sure you have built the vector store:

```python
from agents.vector_store import build_schema_vector_store
build_schema_vector_store()
```

## UI Pages

### 1. Overview
- Displays all available collections
- Shows document counts and metadata samples
- Provides quick statistics

### 2. Browse Documents
- Lists all documents in the vector store
- Filter by table name or database type
- View full document content and metadata

### 3. Search
- Semantic search using natural language queries
- Adjustable number of results (1-10)
- Shows similarity scores for each result
- Displays full schema information for matches

### 4. Statistics
- Overall statistics (collections, documents, tables)
- Per-collection details
- Database type distribution charts
- Table listings per collection

## File Structure

```
ui_db_schema/
├── app.py          # Main Streamlit application
├── utils.py        # Utility functions for vector store operations
├── ui_config.py    # Configuration settings
├── __init__.py     # Module initialization
└── README.md       # This file
```

## Configuration

The UI reads configuration from `config.vector_config`:
- `VECTOR_DB_SCHEMA_DIR`: Directory containing vector databases
- `VECTOR_DB_SCHEMA_NAME`: Base name for schema collections

## Features in Detail

### Caching
- Results are cached for 5 minutes to improve performance
- Use the "Refresh Data" button to clear cache and reload

### Filtering
- Filter documents by table name (case-insensitive)
- Filter by database type
- Multiple filters can be applied simultaneously

### Search
- Uses semantic similarity search
- Returns results ranked by relevance
- Shows detailed metadata for each result

## Troubleshooting

### No vector store found
If you see "No vector store found", you need to build it first:
```python
from agents.vector_store import build_schema_vector_store
build_schema_vector_store()
```

### Import errors
Make sure you're running from the correct directory or that the parent directories are in your Python path.

### Empty results
Ensure your database connection is configured and the vector store has been populated with data.

## Development

To extend the UI:
1. Add new utility functions in `utils.py`
2. Create new pages in `app.py`
3. Update styling in the CSS section of `app.py`
4. Add new configuration options in `ui_config.py`
