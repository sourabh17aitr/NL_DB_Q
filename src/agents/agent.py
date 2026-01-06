from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain.agents.middleware import TodoListMiddleware 

from src.config.prompt import system_prompt, OLLAMA_REACT_PROMPT
from src.agents.tools import db_tool_manager

# Cache for agents
_agents_cache = {}

def get_llm(provider: str, model: str):
    """Get LLM instance."""
    kwargs = {"model": model, "temperature": 0}
    if provider == "OpenAI": return ChatOpenAI(**kwargs)
    if provider == "Anthropic": return ChatAnthropic(**kwargs)
    if provider == "Groq": return ChatGroq(**kwargs)
    if provider == "Gemini": return ChatGoogleGenerativeAI(**kwargs)
    if provider == "Ollama": return ChatOllama(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")

def get_agent(provider: str, model: str):
    """Get cached agent."""
    key = f"{provider}:{model}"
    if key not in _agents_cache:
        checkpointer = MemorySaver()
        llm = get_llm(provider, model)
        tools = db_tool_manager.get_tools()
        prompt = OLLAMA_REACT_PROMPT if provider == "Ollama" else system_prompt
        
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=prompt,
            checkpointer=checkpointer,
            middleware=[TodoListMiddleware()] 
        )
        _agents_cache[key] = agent
    return _agents_cache[key]

def stream_agent(agent, prompt, config):
    yield from agent.stream(
        {"messages": [("user", prompt)]}, 
        config, 
        stream_mode=["messages", "updates"]  # Both token + step streaming
    )