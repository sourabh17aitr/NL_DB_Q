"""Agent creation and streaming logic for database querying."""
import logging
from typing import Dict, Any, Iterator

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents.middleware import TodoListMiddleware

from config.prompt import system_prompt, OLLAMA_REACT_PROMPT
from agents.tools import db_tool_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Cache for agents
_agents_cache: Dict[str, Any] = {}


def get_agent(provider: str, model: str) -> Any:
    """Get or create cached agent for the given provider and model.
    
    Args:
        provider: LLM provider name (e.g., 'openai', 'anthropic', 'ollama')
        model: Model name (e.g., 'gpt-4o', 'claude-3-5-sonnet')
        
    Returns:
        Configured agent with tools and checkpointer
    """
    key = f"{provider}:{model}"
    if key not in _agents_cache:
        checkpointer = MemorySaver()
        llm = init_chat_model(key, temperature=0)
        tools = db_tool_manager.get_tools(llm=llm)
        prompt = OLLAMA_REACT_PROMPT if provider.lower() == "ollama" else system_prompt
        
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=prompt,
            checkpointer=checkpointer,
            middleware=[TodoListMiddleware()] 
        )
        _agents_cache[key] = agent
        logger.info(f"Created new langchain agent for {key}")
    return _agents_cache[key]

def stream_agent(agent: Any, prompt: str, config: Dict[str, Any]) -> Iterator[Any]:
    """Stream agent responses with messages and updates.
    
    Args:
        agent: The agent instance to stream from
        prompt: User prompt/question
        config: Configuration dict with thread_id and other settings
        
    Yields:
        Stream chunks containing messages and updates
    """
    yield from agent.stream(
        {"messages": [("user", prompt)]}, 
        config, 
        stream_mode=["messages", "updates"]
    )