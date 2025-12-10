import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from src.agents.tools.db_tools import DBToolManager
from src.config.prompt import system_prompt, OLLAMA_REACT_PROMPT

logger = logging.getLogger(__name__)

def _create_agent(llm_provider: str, model_name: str):
    """Agent factory: Create agent for llm provider/model.""" 
    # Create model
    model = _get_model(llm_provider, model_name)    
    # Define tools
    tool_mgr = DBToolManager()
    tools = tool_mgr.get_tools()
    # Create agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt= OLLAMA_REACT_PROMPT if llm_provider == "Ollama" else system_prompt,
        checkpointer= MemorySaver()
    )
    return agent

def _get_model(provider: str, model_name: str):
    """Model factory"""
    try:
        if provider == "OpenAI": return ChatOpenAI(model=model_name, temperature=0)
        elif provider == "Anthropic": return ChatAnthropic(model=model_name, temperature=0)
        elif provider == "Groq": return ChatGroq(model=model_name, temperature=0)
        elif provider == "Gemini": return ChatGoogleGenerativeAI(model=model_name, temperature=0)
        elif provider == "Ollama": return ChatOllama(model=model_name, temperature=0)
        else: raise ValueError(f"Unknown provider: {provider}")
    except Exception as e:
        logger.error(f"❌ Model Factory Error: {e}")
        raise