"""
LLM Client for Ollama Integration
Handles communication with local Ollama models
"""

import requests
import json
import os
from typing import List, Dict, Optional, Generator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OllamaClient:
    """Client for interacting with Ollama local LLM models"""
    
    def __init__(self, base_url: str = None):
        # Use environment variable if available, otherwise default to localhost
        self.base_url = base_url or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        # No hardcoded models - fetch from Ollama at runtime
        self.current_model = None
        self.conversation_history: List[Dict[str, str]] = []
        
    def set_model(self, model_name: str) -> bool:
        """Set the current model to use"""
        # Always allow setting the model (validation happens at generate time)
        self.current_model = model_name
        return True
    
    def clear_context(self):
        """Clear conversation history for new context"""
        self.conversation_history = []
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                # Set first model as current if none set
                if model_names and not self.current_model:
                    self.current_model = model_names[0]
                return model_names
            print(f"⚠️ Ollama returned status {response.status_code}")
            return []
        except requests.exceptions.ConnectionError:
            print(f"⚠️ Cannot connect to Ollama at {self.base_url}")
            print(f"   Make sure Ollama is running and accessible")
            return []
        except Exception as e:
            print(f"⚠️ Error fetching models: {e}")
            return []
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        keep_context: bool = False,
        stream: bool = False
    ) -> Dict[str, any]:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The user prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            keep_context: Whether to maintain conversation context
            stream: Whether to stream the response
            
        Returns:
            Dict with response, raw_output, and metadata
        """
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if keep_context and self.conversation_history:
            messages.extend(self.conversation_history)
        
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request
        payload = {
            "model": self.current_model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=stream
            )
            
            if stream:
                return self._handle_streaming_response(response, messages)
            else:
                return self._handle_response(response, messages, keep_context)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "",
                "raw_output": "",
                "model": self.current_model
            }
    
    def _handle_response(self, response, messages: List[Dict], keep_context: bool) -> Dict:
        """Handle non-streaming response"""
        if response.status_code == 200:
            result = response.json()
            assistant_message = result.get('message', {}).get('content', '')
            
            # Update conversation history if keeping context
            if keep_context:
                self.conversation_history.append(messages[-1])  # User message
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
            
            return {
                "success": True,
                "response": assistant_message,
                "raw_output": json.dumps(result, indent=2),
                "model": self.current_model,
                "prompt_tokens": result.get('prompt_eval_count', 0),
                "completion_tokens": result.get('eval_count', 0),
                "total_duration": result.get('total_duration', 0)
            }
        else:
            error_text = response.text
            error_msg = f"HTTP {response.status_code}: {error_text}"
            
            # Check for context overflow specifically
            if any(keyword in error_text.lower() for keyword in ["context", "too long", "max", "overflow", "exceed"]):
                error_msg = f"🔴 CONTEXT OVERFLOW: Input exceeds model's maximum context length ({response.status_code}). Try: 1) Reduce submission size, 2) Simplify rubric, 3) Use model with larger context (e.g., codellama has 16K tokens)"
            
            return {
                "success": False,
                "error": error_msg,
                "response": "",
                "raw_output": error_text,
                "model": self.current_model
            }
    
    def _handle_streaming_response(self, response, messages: List[Dict]) -> Generator:
        """Handle streaming response (for future use)"""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if 'message' in chunk:
                        yield chunk['message'].get('content', '')
                except json.JSONDecodeError:
                    continue
    
    def test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def pull_model(self, model_name: str) -> Dict:
        """Pull a model from Ollama repository"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            )
            return {
                "success": response.status_code == 200,
                "message": "Model pulled successfully" if response.status_code == 200 else response.text
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

