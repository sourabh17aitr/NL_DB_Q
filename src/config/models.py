llm_providers = ["OpenAI", "Anthropic", "Groq", "Gemini", "Ollama"]
model_options = {
    "Gemini": ["gemini-3-pro-preview","gemini-1.5-pro", "gemini-1.5-flash"],
    "OpenAI": ["gpt-4o", "gpt-4o-mini"],
    "Anthropic": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    "Groq": ["llama3-70b-8192", "mixtral-8x7b-32768"],
    "Ollama": ["llama3-groq-tool-use"]
}
default_llm = {
    "provider": "Ollama",
    "model": "llama3-groq-tool-use"
}

