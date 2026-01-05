"""
Google Gemini provider implementation.
"""

from typing import List, Dict, Any, Optional
import google.generativeai as genai

from contextmemory.core.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini provider using the official Google SDK."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key (Gemini API key)
        """
        genai.configure(api_key=api_key)
        self.api_key = api_key
    
    def _convert_messages_to_gemini_format(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Convert OpenAI-style messages to Gemini format.
        
        Gemini uses 'user' and 'model' roles instead of 'assistant'.
        System messages are handled differently in Gemini.
        """
        gemini_messages = []
        system_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_parts.append(content)
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
        
        return gemini_messages, "\n".join(system_parts) if system_parts else None
    
    def _convert_tool_calls_to_gemini(
        self, tool_calls: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Convert OpenAI tool calls to Gemini function calling format.
        
        Note: Gemini's function calling format is different from OpenAI.
        This is a simplified conversion - full support may require more work.
        """
        if not tool_calls:
            return None
        
        # For now, we'll extract the first tool call
        # Full implementation would need to handle multiple tool calls
        tool_call = tool_calls[0]
        return {
            "name": tool_call["function"]["name"],
            "args": tool_call["function"]["arguments"],
        }
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Gemini.
        
        Note: Gemini's function calling support is different from OpenAI.
        This implementation provides basic support.
        """
        gemini_messages, system_instruction = self._convert_messages_to_gemini_format(messages)
        
        # Configure the model
        genai_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction if system_instruction else None,
        )
        
        # Convert tools to Gemini format if provided
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
        )
        
        # Start a chat session
        chat = genai_model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
        
        # Send the last message
        last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""
        
        response = chat.send_message(
            last_message,
            generation_config=generation_config,
        )
        
        result = {
            "content": response.text or "",
        }
        
        # Handle function calling if present
        if hasattr(response, "function_calls") and response.function_calls:
            result["tool_calls"] = [
                {
                    "id": f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": str(fc.args),
                    },
                }
                for i, fc in enumerate(response.function_calls)
            ]
        
        return result
    
    def create_embedding(
        self,
        model: str,
        text: str,
    ) -> List[float]:
        """
        Create an embedding using Gemini.
        
        Note: Gemini uses 'models/embedding-001' or 'models/text-embedding-004'
        for embeddings. The model parameter should match these.
        """
        result = genai.embed_content(
            model=model,
            content=text,
            task_type="retrieval_document",  # or "retrieval_query", "semantic_similarity", etc.
        )
        return result["embedding"]
    
    def get_default_chat_model(self) -> str:
        """Get default Gemini chat model."""
        return "gemini-1.5-flash"
    
    def get_default_embedding_model(self) -> str:
        """Get default Gemini embedding model."""
        return "models/text-embedding-004"

