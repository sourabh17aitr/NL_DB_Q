from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings, OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

llm_providers = ["openai", "anthropic", "groq", "gemini", "ollama"]
model_options = {
    "gemini": ["gemini-3-pro-preview","gemini-1.5-pro", "gemini-1.5-flash"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    "groq": ["llama3-70b-8192", "mixtral-8x7b-32768"],
    "ollama": ["llama3.1:8b","llama3-groq-tool-use"]
}
default_llm = {
    "provider": "openai",
    "model": "gpt-4o"
}

def get_llm_key():
    return f"{default_llm['provider']}:{default_llm['model']}"

def get_llm():
    llm = init_chat_model(get_llm_key(), temperature=0)
    return llm

embedding_models = {
    "openai": ["text-embedding-3-small", "text-embedding-3-large"],
    "ollama": ["nomic-embed-text", "mxbai-embed-large"],
    "gemini": ["models/embedding-001"]
}
default_embedding_model = {
    "provider": "openai",
    "model": "text-embedding-3-small"
}

def get_vector_embeddings():
    provider = default_embedding_model["provider"]
    model = default_embedding_model["model"]
    
    embedding_registry = {
        "openai": lambda m: OpenAIEmbeddings(model=m),
        "huggingface": lambda m: HuggingFaceEmbeddings(model_name=m),
        "ollama": lambda m: OllamaEmbeddings(model=m),
        "gemini": lambda m: GoogleGenerativeAIEmbeddings(model=m)
    }
    
    if provider not in embedding_registry:
        raise ValueError(f"Unsupported embedding provider: {provider}. Available: {list(embedding_registry.keys())}")
    
    return embedding_registry[provider](model)
