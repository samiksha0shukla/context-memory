"""
Google Gemini provider implementation.
"""

from typing import List, Dict, Any, Optional
import json
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from contextmemory.core.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini provider using the official Google SDK."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google AI API key (Gemini API key)
        """
        if genai is None:
            raise ImportError(
                "google-generativeai package is required for Gemini provider. "
                "Install it with: pip install google-generativeai"
            )
        genai.configure(api_key=api_key)
        self.api_key = api_key
    
    def _convert_messages_to_gemini_format(
        self, messages: List[Dict[str, str]]
    ) -> tuple[List[Dict[str, str]], Optional[str]]:
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
    
    def _convert_tools_to_gemini_format(
        self, tools: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Any]]:
        """
        Convert OpenAI tools format to Gemini function declarations.
        
        Gemini uses a different format for function calling.
        Note: This is a simplified implementation. Full function calling
        support may require additional work depending on Gemini API version.
        """
        if not tools:
            return None
        
        try:
            gemini_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    # Convert OpenAI function format to Gemini format
                    gemini_tool = genai.protos.FunctionDeclaration(
                        name=func.get("name"),
                        description=func.get("description", ""),
                        parameters=self._convert_schema_to_gemini(func.get("parameters", {})),
                    )
                    gemini_tools.append(genai.protos.Tool(function_declarations=[gemini_tool]))
            
            return gemini_tools if gemini_tools else None
        except Exception:
            # If conversion fails, return None (function calling won't work)
            # This allows the provider to still work for non-function-calling use cases
            return None
    
    def _convert_schema_to_gemini(self, schema: Dict[str, Any]) -> Any:
        """Convert JSON schema to Gemini Schema format."""
        # This is a simplified conversion
        # Full implementation would need to handle all schema types
        try:
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            gemini_properties = {}
            for prop_name, prop_schema in properties.items():
                prop_type = prop_schema.get("type", "string")
                gemini_properties[prop_name] = genai.protos.Schema(
                    type_=self._map_type_to_gemini(prop_type),
                    description=prop_schema.get("description", ""),
                )
            
            return genai.protos.Schema(
                type_=genai.protos.Type.OBJECT,
                properties=gemini_properties,
                required=required,
            )
        except Exception:
            # Fallback to simple string schema if conversion fails
            return genai.protos.Schema(type_=genai.protos.Type.STRING)
    
    def _map_type_to_gemini(self, json_type: str) -> Any:
        """Map JSON schema type to Gemini Schema type."""
        type_map = {
            "string": genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number": genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array": genai.protos.Type.ARRAY,
            "object": genai.protos.Type.OBJECT,
        }
        return type_map.get(json_type, genai.protos.Type.STRING)
    
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
        genai_tools = self._convert_tools_to_gemini_format(tools)
        
        genai_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction if system_instruction else None,
            tools=genai_tools if genai_tools else None,
        )
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
        )
        
        # Start a chat session with history
        history = gemini_messages[:-1] if len(gemini_messages) > 1 else []
        chat = genai_model.start_chat(history=history)
        
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
                        "arguments": json.dumps(dict(fc.args)) if hasattr(fc.args, '__iter__') and not isinstance(fc.args, str) else str(fc.args),
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

