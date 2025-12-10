import logging
from typing import Dict, Any, Generator
from langgraph.checkpoint.memory import MemorySaver
from src.agents.agent_factory import _create_agent

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        self.agents = {}
    
    def get_agent(self, provider: str, model_name: str):
        """Get or create agent for provider/model combo."""
        key = f"{provider}:{model_name}"
        
        if key not in self.agents:
            self.agents[key] = self.create_agent(provider, model_name)        
        return self.agents[key]
    
    def create_agent(self, provider: str, model_name: str):
        """Create agent instance."""
        try:
            agent = _create_agent(provider, model_name)
            return agent
        except Exception as e:
            logger.error(f"❌ Agent creation failed: {e}")
            raise
    
    def invoke_agent(self, agent, question: str, config: Dict[str, Any]):
        """Synchronous agent invocation."""
        logger.info(f"🚀 Invoke: '{question[:50]}...'")
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config
        )
        return result
    
    def stream_agent(self, agent, question: str, config: Dict[str, Any]) -> Generator:
        """Stream agent with step tracking."""
        logger.info(f"📡 Stream: '{question[:50]}...' (thread: {config.get('configurable', {}).get('thread_id')})")
        chunk_count = 0
        
        try:
            stream = agent.stream(
                {"messages": [{"role": "user", "content": question}]},
                config,
                stream_mode="values"
            )
            
            for chunk in stream:
                chunk_count += 1
                logger.debug(f"📦 Chunk {chunk_count}")
                yield chunk  # Pass through for UI consumption
            
            logger.info(f"✅ Stream complete: {chunk_count} chunks")
            
        except Exception as e:
            logger.error(f"❌ Stream failed: {e}")
            raise

# Global singleton
agent_manager = AgentManager()