#!/usr/bin/env python3
"""
Unified AI Client
Provides a unified interface for multiple AI providers (Gemini, Claude, OpenAI)
"""

import json
import logging
from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIClient(Protocol):
    """Protocol for AI clients"""
    
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate content using the AI provider"""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Test AI provider connectivity"""
        ...
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get API usage information"""
        ...

class GeminiClient:
    """Gemini AI client"""
    
    def __init__(self, config):
        """Initialize Gemini client"""
        self.config = config
        
        try:
            import google.generativeai as genai
            self.genai = genai
        except ImportError:
            raise ImportError("google-generativeai package required for Gemini support")
        
        if not self.config.is_valid():
            raise ValueError("Invalid Gemini configuration")
        
        # Configure Gemini API
        self.genai.configure(api_key=self.config.api_key)
        
        # Initialize model with optimized settings
        self.model = self.genai.GenerativeModel(
            model_name=self.config.model_name,
            generation_config=self.genai.types.GenerationConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=self.config.max_output_tokens,
                response_mime_type="application/json"
            )
        )
        
        logger.info(f"🤖 Gemini client initialized: {self.config.model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_content(self, prompt: str, output_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Generate content with Gemini"""
        try:
            # For text output, modify the model configuration temporarily
            if output_format == "text":
                # Create a model without JSON constraint for text output
                text_model = self.genai.GenerativeModel(
                    model_name=self.config.model_name,
                    generation_config=self.genai.types.GenerationConfig(
                        temperature=self.config.temperature,
                        top_p=self.config.top_p,
                        top_k=self.config.top_k,
                        max_output_tokens=self.config.max_output_tokens
                        # No response_mime_type for text output
                    )
                )
                response = text_model.generate_content(prompt)
            else:
                response = self.model.generate_content(prompt)
            
            if response.text:
                if output_format == "text":
                    return {"content": response.text}
                else:
                    try:
                        return json.loads(response.text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Gemini response as JSON: {e}")
                        return {"content": response.text, "error": "json_parse_failed"}
            else:
                logger.warning("Empty response from Gemini")
                return {"error": "empty_response"}
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Test Gemini API connectivity"""
        try:
            test_prompt = """
            Generate a simple JSON response with a test message.
            Format: {"message": "API test successful", "status": "healthy"}
            """
            
            response = self.generate_content(test_prompt)
            
            if "error" in response:
                return {"status": "unhealthy", "error": response["error"]}
            
            return {
                "status": "healthy",
                "model": self.config.model_name,
                "provider": "gemini",
                "response_received": bool(response)
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get Gemini usage information"""
        return {
            "provider": "gemini",
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "api_key_hash": self.config.api_key[:8] + "..." if self.config.api_key else None
        }

class ClaudeClient:
    """Claude AI client"""
    
    def __init__(self, config):
        """Initialize Claude client"""
        self.config = config
        
        try:
            import anthropic
            self.anthropic = anthropic
        except ImportError:
            raise ImportError("anthropic package required for Claude support")
        
        if not self.config.is_valid():
            raise ValueError("Invalid Claude configuration")
        
        # Initialize Claude client
        self.client = self.anthropic.Anthropic(api_key=self.config.api_key)
        
        logger.info(f"🤖 Claude client initialized: {self.config.model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_content(self, prompt: str, output_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Generate content with Claude"""
        try:
            # Format prompt based on output type
            if output_format == "text":
                formatted_prompt = prompt
            else:
                formatted_prompt = f"""
{prompt}

Please respond with valid JSON only. Do not include any text before or after the JSON.
"""
            
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ]
            )
            
            if response.content and len(response.content) > 0:
                content_text = response.content[0].text
                
                # For text output, return as-is
                if output_format == "text":
                    return {"content": content_text}
                
                # Clean up Claude's markdown formatting for JSON
                content_text = content_text.strip()
                if content_text.startswith('```json'):
                    content_text = content_text[7:]  # Remove ```json
                if content_text.startswith('```'):
                    content_text = content_text[3:]   # Remove ```
                if content_text.endswith('```'):
                    content_text = content_text[:-3]  # Remove trailing ```
                content_text = content_text.strip()
                
                try:
                    return json.loads(content_text)
                except json.JSONDecodeError as e:
                    # More robust JSON extraction for Claude responses
                    import re
                    try:
                        # Try to find JSON object patterns
                        json_patterns = [
                            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
                            r'\{[\s\S]*?\}',  # Any JSON-like structure
                        ]
                        
                        for pattern in json_patterns:
                            matches = re.findall(pattern, content_text)
                            for match in matches:
                                try:
                                    return json.loads(match)
                                except json.JSONDecodeError:
                                    continue
                        
                        # If no valid JSON found, create structured response
                        logger.warning(f"Claude returned non-JSON response: {content_text[:100]}...")
                        return {
                            "content": content_text,
                            "ai_provider": "claude", 
                            "parsed": False,
                            "fallback": True
                        }
                        
                    except Exception as fallback_e:
                        logger.error(f"Failed to parse Claude response as JSON with fallback: {e}")
                        logger.debug(f"Raw content: {repr(content_text[:200])}")
                        return {"content": content_text, "error": "json_parse_failed"}
            else:
                logger.warning("Empty response from Claude")
                return {"error": "empty_response"}
                
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Test Claude API connectivity"""
        try:
            test_prompt = """
            Generate a simple JSON response with a test message.
            Format: {"message": "API test successful", "status": "healthy"}
            """
            
            response = self.generate_content(test_prompt)
            
            if "error" in response:
                return {"status": "unhealthy", "error": response["error"]}
            
            return {
                "status": "healthy",
                "model": self.config.model_name,
                "provider": "claude",
                "response_received": bool(response)
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get Claude usage information"""
        return {
            "provider": "claude",
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "api_key_hash": self.config.api_key[:8] + "..." if self.config.api_key else None
        }

class OpenAIClient:
    """OpenAI client"""
    
    def __init__(self, config):
        """Initialize OpenAI client"""
        self.config = config
        
        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError("openai package required for OpenAI support")
        
        if not self.config.is_valid():
            raise ValueError("Invalid OpenAI configuration")
        
        # Initialize OpenAI client
        self.client = self.openai.OpenAI(api_key=self.config.api_key)
        
        logger.info(f"🤖 OpenAI client initialized: {self.config.model_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_content(self, prompt: str, output_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Generate content with OpenAI"""
        try:
            # Format prompt and request based on output type
            if output_format == "text":
                formatted_prompt = prompt
                response_format = None  # No JSON constraint for text
            else:
                formatted_prompt = f"""
{prompt}

Please respond with valid JSON only. Do not include any text before or after the JSON.
"""
                response_format = {"type": "json_object"}  # Force JSON output
            
            create_params = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": formatted_prompt}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
            
            if response_format:
                create_params["response_format"] = response_format
                
            response = self.client.chat.completions.create(**create_params)
            
            if response.choices and len(response.choices) > 0:
                content_text = response.choices[0].message.content
                
                if output_format == "text":
                    return {"content": content_text}
                else:
                    try:
                        return json.loads(content_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                        return {"content": content_text, "error": "json_parse_failed"}
            else:
                logger.warning("Empty response from OpenAI")
                return {"error": "empty_response"}
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Test OpenAI API connectivity"""
        try:
            test_prompt = """
            Generate a simple JSON response with a test message.
            Format: {"message": "API test successful", "status": "healthy"}
            """
            
            response = self.generate_content(test_prompt)
            
            if "error" in response:
                return {"status": "unhealthy", "error": response["error"]}
            
            return {
                "status": "healthy",
                "model": self.config.model_name,
                "provider": "openai",
                "response_received": bool(response)
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get OpenAI usage information"""
        return {
            "provider": "openai",
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "api_key_hash": self.config.api_key[:8] + "..." if self.config.api_key else None
        }

class UnifiedAIClient:
    """Unified client that works with multiple AI providers"""
    
    def __init__(self, config):
        """Initialize unified AI client"""
        self.config = config.ai
        self.provider = config.ai.provider
        
        # Check if using demo/test keys and use mock client
        provider_config = self.config.get_current_provider_config()
        if self._is_demo_key(provider_config.api_key):
            from .mock_client import MockAIClient
            self.client = MockAIClient(config)
            logger.info(f"🎭 Using Mock AI Client (demo mode) with provider: {self.provider.value}")
        else:
            # Initialize the appropriate client based on provider
            if self.provider.value == "gemini":
                self.client = GeminiClient(self.config.gemini)
            elif self.provider.value == "claude":
                self.client = ClaudeClient(self.config.claude)
            elif self.provider.value == "openai":
                self.client = OpenAIClient(self.config.openai)
            else:
                raise ValueError(f"Unsupported AI provider: {self.provider}")
            
            logger.info(f"🤖 Unified AI Client initialized with provider: {self.provider.value}")
    
    def _is_demo_key(self, api_key: str) -> bool:
        """Check if the API key is a demo/test key"""
        demo_patterns = [
            'demo', 'test', 'mock', 'fake', 'example',
            'AIzaSyDemoKeyForTestingPurposesOnly',
            'sk-demo-', 'test_', 'demo_'
        ]
        return any(pattern in api_key.lower() for pattern in demo_patterns)
    
    def generate_content(self, prompt: str, output_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Generate content using the selected AI provider"""
        try:
            # Modify prompt based on output format
            if output_format == "text":
                # For text output, remove JSON formatting instructions
                modified_prompt = prompt
                if "Please respond with valid JSON only" in prompt:
                    modified_prompt = prompt.replace("Please respond with valid JSON only. Do not include any text before or after the JSON.", "")
            else:
                modified_prompt = prompt
            
            result = self.client.generate_content(modified_prompt, output_format=output_format, **kwargs)
            
            # Handle different output formats
            if output_format == "text" and isinstance(result, dict):
                # For text format, wrap the content in a standard structure
                if "content" not in result and len(result) > 0:
                    # If result is parsed JSON, convert back to text
                    content_text = str(result)
                    result = {"content": content_text}
            
            # Add provider metadata to result
            if isinstance(result, dict):
                result["ai_provider"] = self.provider.value
                result["model_name"] = self.config.get_current_provider_config().model_name
                result["output_format"] = output_format
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating content with {self.provider.value}: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Test current AI provider connectivity"""
        return self.client.health_check()
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get current AI provider usage information"""
        usage_info = self.client.get_usage_info()
        usage_info["current_provider"] = self.provider.value
        return usage_info
    
    def switch_provider(self, new_provider: str, config):
        """Switch to a different AI provider"""
        try:
            from core.config import AIProvider
            
            provider = AIProvider(new_provider.lower())
            
            if provider == AIProvider.GEMINI:
                self.client = GeminiClient(config.ai.gemini)
            elif provider == AIProvider.CLAUDE:
                self.client = ClaudeClient(config.ai.claude)
            elif provider == AIProvider.OPENAI:
                self.client = OpenAIClient(config.ai.openai)
            
            self.provider = provider
            logger.info(f"🔄 Switched AI provider to: {provider.value}")
            
        except Exception as e:
            logger.error(f"Failed to switch to provider {new_provider}: {e}")
            raise
    
    def get_available_providers(self, config) -> List[str]:
        """Get list of available providers with valid configurations"""
        available = []
        
        if config.ai.gemini and config.ai.gemini.is_valid():
            available.append("gemini")
        if config.ai.claude and config.ai.claude.is_valid():
            available.append("claude")
        if config.ai.openai and config.ai.openai.is_valid():
            available.append("openai")
        
        return available
