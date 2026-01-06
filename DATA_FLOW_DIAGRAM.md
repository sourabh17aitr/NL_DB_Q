# NLDBQ Data Flow Diagram

## High-Level Architecture

```mermaid
graph TB
    User[👤 User] -->|Natural Language Query| UI[🖥️ Streamlit UI]
    UI -->|Initialize Agent| AM[🤖 Agent Manager]
    AM -->|Create Agent| AF[🏭 Agent Factory]
    AF -->|Select LLM| LLM[🧠 LLM Provider]
    
    UI -->|Stream Query| Agent[🤖 NLDBQ Agent]
    Agent -->|Use Tools| Tools[🔧 DB Tools]
    Tools -->|Query Schema| Schema[📊 Schema Wrapper]
    Schema -->|Connect| DB[🗄️ Database]
    
    Agent -->|Generate SQL| Validator[✅ SQL Validator]
    Validator -->|Execute Safe SQL| DB
    DB -->|Results| Agent
    Agent -->|Stream Steps & Response| UI
    UI -->|Display| User
    
    style User fill:#e1f5ff
    style UI fill:#fff4e1
    style Agent fill:#e8f5e9
    style DB fill:#fce4ec
    style LLM fill:#f3e5f5
```

## Detailed Data Flow

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant UI as 🖥️ Streamlit UI
    participant AM as 🤖 Agent Manager
    participant A as 🤖 Agent
    participant T as 🔧 Tools
    participant S as 📊 Schema Wrapper
    participant DB as 🗄️ Database
    participant LLM as 🧠 LLM
    
    U->>UI: Enter natural language query
    UI->>UI: Add to chat history
    
    Note over UI,AM: Agent Initialization (if needed)
    UI->>AM: get_agent(provider, model)
    AM->>LLM: Initialize LLM client
    AM->>T: Get DB tools
    AM-->>UI: Return configured agent
    
    Note over UI,A: Query Processing
    UI->>A: stream(query, config)
    A->>A: Step 01: Planning next steps
    
    Note over A,DB: Schema Discovery Phase
    A->>T: list_tables()
    T->>S: get_all_tables()
    S->>DB: SELECT table_name FROM information_schema
    DB-->>S: Table list
    S-->>T: Formatted table info
    T-->>A: Available tables
    A->>UI: Step 02: Found tables
    
    A->>T: get_table_info(table_name)
    T->>S: get_table_schema(table_name)
    S->>DB: SELECT column details
    DB-->>S: Column metadata
    S-->>T: Schema details
    T-->>A: Table structure
    A->>UI: Step 03: Analyzing schema
    
    Note over A,LLM: SQL Generation Phase
    A->>LLM: Generate SQL based on schema + query
    LLM-->>A: SQL query
    A->>A: Validate SQL (no DROP/DELETE/etc)
    A->>UI: Step 04: Generated SQL query
    
    Note over A,DB: Execution Phase
    A->>T: execute_sql(query)
    T->>S: execute_query(sql)
    S->>DB: Execute SQL
    DB-->>S: Query results
    S-->>T: Formatted results
    T-->>A: Result set
    A->>UI: Step 05: Found N results
    
    Note over A,LLM: Response Generation
    A->>LLM: Summarize results
    LLM-->>A: Natural language summary
    A->>UI: Step 06: Summarizing findings
    
    A->>UI: Final response with results
    UI->>U: Display answer + SQL + results
    UI->>UI: Save to query history
```

## Component Breakdown

### 1. **User Interface Layer** (`src/ui/`)
```mermaid
graph LR
    A[streamlit_app.py] -->|Imports| B[config.py]
    A -->|Imports| C[chat.py]
    A -->|Imports| D[history.py]
    A -->|Imports| E[utils.py]
    A -->|Calls| F[main_display.py]
    
    style A fill:#fff4e1
```

**Data Flow:**
- User input → Session state
- Session state → Agent manager
- Agent responses → UI components
- Query history → Sidebar display

### 2. **Agent Layer** (`src/agents/`)
```mermaid
graph TB
    A[User Query] -->|Input| B[agent.py]
    B -->|Creates| C[Agent Instance]
    B -->|Configures| D[LLM Provider]
    B -->|Loads| E[tools.py]
    E -->|Provides| F[DB Tools]
    C -->|Uses| F
    C -->|Streams| G[Response Chunks]
    
    style B fill:#e8f5e9
    style C fill:#c8e6c9
```

**Data Flow:**
- Natural language → Agent
- Agent → Tool selection
- Tools → Database operations
- Results → Natural language response

### 3. **Database Layer** (`src/db/`)
```mermaid
graph TB
    A[db_client.py] -->|Manages| B[Connection Pool]
    C[db_schema_wrapper.py] -->|Uses| A
    C -->|Queries| D[information_schema]
    C -->|Executes| E[User Queries]
    D -->|Returns| F[Schema Metadata]
    E -->|Returns| G[Query Results]
    
    style A fill:#fce4ec
    style C fill:#f8bbd0
```

**Data Flow:**
- Schema requests → information_schema queries
- SQL execution → Database
- Results → Formatted output
- Connection management → Pool

### 4. **Configuration Layer** (`src/config/`)
```mermaid
graph LR
    A[models.py] -->|Defines| B[LLM Providers]
    C[prompt.py] -->|Provides| D[System Prompts]
    E[db_schema.py] -->|Defines| F[Schema Structure]
    B -->|Used by| G[Agent Factory]
    D -->|Used by| G
    F -->|Used by| H[Schema Wrapper]
    
    style A fill:#f3e5f5
```

### 5. **Agent Steps Flow**
```mermaid
stateDiagram-v2
    [*] --> Planning: User Query Received
    Planning --> SchemaDiscovery: Step 01: Planning next steps
    SchemaDiscovery --> SQLGeneration: Step 02-03: List tables & analyze schema
    SQLGeneration --> Validation: Generate SQL query
    Validation --> Execution: SQL validated (safe)
    Validation --> Error: SQL rejected (unsafe)
    Execution --> Results: Step 04: Executing query
    Results --> Summarization: Step 05: Found N results
    Summarization --> Response: Step 06: Summarizing findings
    Response --> [*]: Display to user
    Error --> [*]: Show error message
```

## Data Structures

### Query Processing Data Flow
```
Input: Natural Language String
  ↓
Agent State: {
  messages: [HumanMessage, AIMessage, ToolMessage],
  thread_id: "conversation_1",
  config: {...}
}
  ↓
Tool Calls: {
  name: "list_tables" | "get_table_info" | "execute_sql",
  args: {...},
  results: {...}
}
  ↓
LLM Response: {
  content: "Natural language answer",
  tool_calls: [...],
  type: "ai"
}
  ↓
Output: Formatted Response + SQL + Results
```

### Session State Structure
```
st.session_state = {
  messages: [
    {role: "user", content: "..."},
    {role: "assistant", content: "..."}
  ],
  query_history: [
    {
      question: "...",
      sql: "SELECT ...",
      timestamp: datetime
    }
  ],
  agent: Agent,
  current_agent_key: "provider:model",
  config: {
    configurable: {
      thread_id: "..."
    }
  }
}
```

## Tool Execution Flow

```mermaid
graph TB
    A[Agent Decides Tool] -->|list_tables| B[List All Tables]
    A -->|get_table_info| C[Get Table Schema]
    A -->|execute_sql| D[Execute SQL Query]
    
    B -->|Query| E[information_schema.tables]
    C -->|Query| F[information_schema.columns]
    D -->|Validate| G{Safe SQL?}
    
    G -->|Yes| H[Execute on DB]
    G -->|No| I[Reject & Error]
    
    H -->|Results| J[Format Output]
    I -->|Message| K[Error Response]
    
    E -->|Data| L[Tool Result]
    F -->|Data| L
    J -->|Data| L
    K -->|Error| L
    
    L -->|Return| M[Agent Processes]
    M -->|Next Step| A
    M -->|Final Answer| N[User Response]
    
    style G fill:#fff59d
    style I fill:#ffcdd2
    style N fill:#c8e6c9
```

## Environment Variables Flow

```mermaid
graph LR
    A[.env file] -->|Load| B[Environment]
    B -->|OPENAI_API_KEY| C[OpenAI Client]
    B -->|ANTHROPIC_API_KEY| D[Anthropic Client]
    B -->|GROQ_API_KEY| E[Groq Client]
    B -->|GOOGLE_API_KEY| F[Gemini Client]
    B -->|DB_CONNECTION_STRING| G[Database Client]
    
    C -->|Used by| H[Agent]
    D -->|Used by| H
    E -->|Used by| H
    F -->|Used by| H
    G -->|Used by| I[DB Tools]
    
    H -->|Queries| I
    I -->|Results| H
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
```

## Error Handling Flow

```mermaid
graph TB
    A[User Query] --> B{Agent Available?}
    B -->|No| C[Error: Load Agent First]
    B -->|Yes| D{Valid Query?}
    
    D -->|No| E[Error: Invalid Input]
    D -->|Yes| F[Process Query]
    
    F --> G{Tool Execution}
    G -->|DB Error| H[Catch Exception]
    G -->|Success| I[Get Results]
    
    I --> J{Valid SQL?}
    J -->|Unsafe| K[Error: SQL Rejected]
    J -->|Safe| L[Execute]
    
    L --> M{Execution Success?}
    M -->|Error| N[Display DB Error]
    M -->|Success| O[Return Results]
    
    H -->|Log| P[Error Message]
    K -->|Log| P
    N -->|Display| Q[User Sees Error]
    P -->|Display| Q
    
    O -->|Format| R[Success Response]
    R -->|Display| S[User Sees Answer]
    
    style C fill:#ffcdd2
    style E fill:#ffcdd2
    style K fill:#ffcdd2
    style N fill:#ffcdd2
    style S fill:#c8e6c9
```

## Streaming Architecture

```mermaid
graph TB
    A[Agent Stream] -->|Chunk 1| B[Step: Planning]
    A -->|Chunk 2| C[Step: Tool Call]
    A -->|Chunk 3| D[Step: Tool Result]
    A -->|Chunk 4| E[Step: Summarizing]
    A -->|Chunk 5| F[Final Response]
    
    B -->|Update| G[steps_placeholder]
    C -->|Update| G
    D -->|Update| G
    E -->|Update| G
    
    F -->|Update| H[message_placeholder]
    
    G -->|Render| I[Agent Steps UI]
    H -->|Render| J[Response UI]
    
    I -->|Display| K[User Sees Steps]
    J -->|Display| K
    
    style A fill:#e1f5ff
    style I fill:#fff4e1
    style J fill:#e8f5e9
```

## Summary

The NLDBQ application follows a **layered architecture** with clear separation of concerns:

1. **Presentation Layer**: Streamlit UI handles user interaction and displays results
2. **Agent Layer**: LangGraph agent orchestrates the query processing workflow
3. **Tool Layer**: Database tools provide safe schema inspection and SQL execution
4. **Data Layer**: Database client manages connections and executes queries
5. **Configuration Layer**: Manages LLM providers, prompts, and system settings

Data flows **unidirectionally** from user input through the agent workflow to the database and back, with each layer responsible for specific transformations and validations.
