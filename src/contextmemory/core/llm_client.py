"""
Unified LLM client manager.

Provides a single interface for all LLM providers (OpenAI, OpenRouter, Gemini).
"""

from typing import List, Dict, Any, Optional
from contextmemory.core.settings import get_settings
from contextmemory.core.providers import get_provider, BaseProvider

# Global provider instance (lazy initialized)
_provider: Optional[BaseProvider] = None


def get_llm_provider() -> BaseProvider:
    """
    Get or create the LLM provider instance.
    
    Uses lazy initialization - provider is created on first call.
    
    Returns:
        BaseProvider instance
    
    Raises:
        RuntimeError: If provider configuration is invalid
    """
    global _provider
    if _provider is None:
        settings = get_settings()
        settings.validate()
        
        api_key = settings.get_api_key()
        kwargs = {"api_key": api_key}
        
        if settings.base_url:
            kwargs["base_url"] = settings.base_url
        
        _provider = get_provider(settings.provider, **kwargs)
    
    return _provider


def reset_provider() -> None:
    """
    Reset provider to None. Useful for testing.
    """
    global _provider
    _provider = None


# Backward compatibility: keep get_openai_client for existing code
# This will be deprecated but maintained for compatibility
def get_openai_client():
    """
    Legacy function for backward compatibility.
    
    Returns a wrapper that provides OpenAI-compatible interface.
    This allows existing code to continue working.
    
    Deprecated: Use get_llm_provider() instead.
    """
    provider = get_llm_provider()
    
    class OpenAICompatibleWrapper:
        """Wrapper to provide OpenAI-compatible interface."""
        
        def __init__(self, provider: BaseProvider):
            self.provider = provider
            self._default_chat_model = provider.get_default_chat_model()
            self._default_embedding_model = provider.get_default_embedding_model()
        
        class ChatCompletions:
            """OpenAI-compatible chat completions interface."""
            
            def __init__(self, provider: BaseProvider):
                self.provider = provider
                self._default_model = provider.get_default_chat_model()
            
            def create(
                self,
                model: Optional[str] = None,
                messages: Optional[List[Dict[str, str]]] = None,
                temperature: float = 0.7,
                tools: Optional[List[Dict[str, Any]]] = None,
                tool_choice: Optional[str] = None,
                **kwargs
            ):
                model = model or self._default_model
                result = self.provider.chat_completion(
                    model=model,
                    messages=messages or [],
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )
                
                # Return OpenAI-compatible response object
                class Response:
                    def __init__(self, result: Dict[str, Any]):
                        self.choices = [self.Choice(result)]
                    
                    class Choice:
                        def __init__(self, result: Dict[str, Any]):
                            self.message = self.Message(result)
                        
                        class Message:
                            def __init__(self, result: Dict[str, Any]):
                                self.content = result.get("content")
                                self.tool_calls = self._convert_tool_calls(
                                    result.get("tool_calls", [])
                                )
                            
                            def _convert_tool_calls(self, tool_calls: List[Dict[str, Any]]):
                                if not tool_calls:
                                    return None
                                
                                class ToolCall:
                                    def __init__(self, tc: Dict[str, Any]):
                                        self.id = tc.get("id")
                                        self.type = tc.get("type")
                                        self.function = self.Function(tc.get("function", {}))
                                    
                                    class Function:
                                        def __init__(self, func: Dict[str, Any]):
                                            self.name = func.get("name")
                                            self.arguments = func.get("arguments")
                                
                                return [ToolCall(tc) for tc in tool_calls]
                
                return Response(result)
        
        class Embeddings:
            """OpenAI-compatible embeddings interface."""
            
            def __init__(self, provider: BaseProvider):
                self.provider = provider
                self._default_model = provider.get_default_embedding_model()
            
            def create(
                self,
                model: Optional[str] = None,
                input: Optional[str] = None,
                **kwargs
            ):
                model = model or self._default_model
                embedding = self.provider.create_embedding(model=model, text=input or "")
                
                # Return OpenAI-compatible response object
                class Response:
                    def __init__(self, embedding: List[float]):
                        self.data = [self.Data(embedding)]
                    
                    class Data:
                        def __init__(self, embedding: List[float]):
                            self.embedding = embedding
                
                return Response(embedding)
        
        def __init__(self, provider: BaseProvider):
            self.provider = provider
            self.chat = self.ChatCompletions(provider)
            self.embeddings = self.Embeddings(provider)
    
    return OpenAICompatibleWrapper(provider)

