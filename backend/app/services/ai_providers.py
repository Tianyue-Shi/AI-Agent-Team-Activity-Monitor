"""
AI Provider Abstraction Layer - Supports OpenAI and Claude.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
import json


# =============================================================================
# Response Models
# =============================================================================

class ToolCall(BaseModel):
    """Represents a tool/function the AI wants to call."""
    name: str                           # Function name (e.g., "get_jira_issues")
    arguments: dict[str, Any]           # Arguments to pass (e.g., {"username": "john"})
    id: str = ""                        # Tool call ID (for matching responses)


class AIResponse(BaseModel):
    """Standard response from any AI provider."""
    content: str                        # The AI's text response
    tool_calls: list[ToolCall] = []     # Any tools the AI wants to call
    model: str = ""                     # Which model was used
    provider: str = ""                  # "openai" or "claude"
    error: Optional[str] = None         # Error message if something went wrong


class Message(BaseModel):
    """A chat message."""
    role: str                           # "system", "user", "assistant", or "tool"
    content: str                        # The message content
    tool_call_id: Optional[str] = None  # For tool responses
    name: Optional[str] = None          # Tool name (for tool responses)
    tool_calls: list["ToolCall"] = []   # For assistant messages with tool calls


# =============================================================================
# Tool Definition Schema
# =============================================================================

class ToolParameter(BaseModel):
    """A parameter for a tool function."""
    name: str
    type: str                           # "string", "integer", "boolean", etc.
    description: str
    required: bool = True


class ToolDefinition(BaseModel):
    """Definition of a tool the AI can call."""
    name: str                           # Function name
    description: str                    # What the function does
    parameters: list[ToolParameter]     # Function parameters


# =============================================================================
# Abstract Base Provider
# =============================================================================

class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All providers must implement:
    - generate(): Basic chat completion
    - generate_with_tools(): Chat with function calling
    """
    
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        system_prompt: str = "",
    ) -> AIResponse:
        """
        Generate a response without tool calling.
        
        Args:
            messages: Conversation history
            system_prompt: System instructions for the AI
            
        Returns:
            AIResponse with the generated text
        """
        pass
    
    @abstractmethod
    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        system_prompt: str = "",
    ) -> AIResponse:
        """
        Generate a response with tool calling capability.
        
        Args:
            messages: Conversation history
            tools: Available tools the AI can call
            system_prompt: System instructions
            
        Returns:
            AIResponse with text and/or tool calls
        """
        pass


# =============================================================================
# OpenAI Provider
# =============================================================================

class OpenAIProvider(AIProvider):
    """
    OpenAI GPT provider.
    
    Uses the official openai Python SDK.
    Supports gpt-5-nano.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-5-nano"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-5-nano)
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def generate(
        self,
        messages: list[Message],
        system_prompt: str = "",
    ) -> AIResponse:
        """Generate response using OpenAI."""
        
        if not self.api_key:
            return AIResponse(
                content="OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file.",
                provider="openai",
                error="missing_api_key"
            )
        
        try:
            client = self._get_client()
            
            # Build messages list
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                openai_messages.append({"role": msg.role, "content": msg.content})
            
            # Call OpenAI
            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
            )
            
            return AIResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                provider="openai",
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Error calling OpenAI: {str(e)}",
                provider="openai",
                error=str(e),
            )
    
    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        system_prompt: str = "",
    ) -> AIResponse:
        """Generate response with function calling."""
        
        if not self.api_key:
            return AIResponse(
                content="OpenAI API key not configured.",
                provider="openai",
                error="missing_api_key"
            )
        
        try:
            client = self._get_client()
            
            # Build messages
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.tool_call_id:
                    msg_dict["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    msg_dict["name"] = msg.name
                # Include tool_calls for assistant messages that made tool calls
                if msg.tool_calls:
                    msg_dict["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                openai_messages.append(msg_dict)
            
            # Convert tools to OpenAI format
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                param.name: {
                                    "type": param.type,
                                    "description": param.description,
                                }
                                for param in tool.parameters
                            },
                            "required": [p.name for p in tool.parameters if p.required],
                        },
                    },
                }
                for tool in tools
            ]
            
            # Call OpenAI with tools
            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools if openai_tools else None,
            )
            
            choice = response.choices[0]
            message = choice.message
            
            # Parse tool calls if any
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(ToolCall(
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                        id=tc.id,
                    ))
            
            return AIResponse(
                content=message.content or "",
                tool_calls=tool_calls,
                model=self.model,
                provider="openai",
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Error calling OpenAI: {str(e)}",
                provider="openai",
                error=str(e),
            )


# =============================================================================
# Claude (Anthropic) Provider
# =============================================================================

class ClaudeProvider(AIProvider):
    """
    Anthropic Claude provider.
    
    Uses the official anthropic Python SDK.
    Supports Claude 3 models (Opus, Sonnet, Haiku).
    """
    
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5"):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use (claude-haiku-4-5)
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def generate(
        self,
        messages: list[Message],
        system_prompt: str = "",
    ) -> AIResponse:
        """Generate response using Claude."""
        
        if not self.api_key:
            return AIResponse(
                content="Anthropic API key not configured. Please add ANTHROPIC_API_KEY to your .env file.",
                provider="claude",
                error="missing_api_key"
            )
        
        try:
            client = self._get_client()
            
            # Claude uses a different format - system is separate
            claude_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
                if msg.role in ["user", "assistant"]
            ]
            
            # Call Claude
            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=claude_messages,
            )
            
            # Extract text from response
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
            
            return AIResponse(
                content=content,
                model=self.model,
                provider="claude",
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Error calling Claude: {str(e)}",
                provider="claude",
                error=str(e),
            )
    
    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolDefinition],
        system_prompt: str = "",
    ) -> AIResponse:
        """Generate response with tool use."""
        
        if not self.api_key:
            return AIResponse(
                content="Anthropic API key not configured.",
                provider="claude",
                error="missing_api_key"
            )
        
        try:
            client = self._get_client()
            
            # Build messages (handle tool results specially)
            claude_messages = []
            pending_tool_results = []
            
            for msg in messages:
                if msg.role == "tool":
                    # Collect tool results to batch into a single user message
                    pending_tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content,
                    })
                elif msg.role == "assistant":
                    # If assistant has tool_calls, include them in content
                    if msg.tool_calls:
                        content_blocks = []
                        if msg.content:
                            content_blocks.append({"type": "text", "text": msg.content})
                        for tc in msg.tool_calls:
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.name,
                                "input": tc.arguments,
                            })
                        claude_messages.append({
                            "role": "assistant",
                            "content": content_blocks,
                        })
                    else:
                        claude_messages.append({
                            "role": "assistant",
                            "content": msg.content,
                        })
                elif msg.role == "user":
                    claude_messages.append({
                        "role": "user",
                        "content": msg.content,
                    })
            
            # Add any pending tool results as a user message
            if pending_tool_results:
                claude_messages.append({
                    "role": "user",
                    "content": pending_tool_results,
                })
            
            # Convert tools to Claude format
            claude_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            param.name: {
                                "type": param.type,
                                "description": param.description,
                            }
                            for param in tool.parameters
                        },
                        "required": [p.name for p in tool.parameters if p.required],
                    },
                }
                for tool in tools
            ]
            
            # Call Claude with tools
            response = await client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=claude_messages,
                tools=claude_tools if claude_tools else None,
            )
            
            # Parse response
            content = ""
            tool_calls = []
            
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
                elif hasattr(block, "type") and block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        name=block.name,
                        arguments=block.input,
                        id=block.id,
                    ))
            
            return AIResponse(
                content=content,
                tool_calls=tool_calls,
                model=self.model,
                provider="claude",
            )
            
        except Exception as e:
            return AIResponse(
                content=f"Error calling Claude: {str(e)}",
                provider="claude",
                error=str(e),
            )


# =============================================================================
# Provider Factory
# =============================================================================

def get_ai_provider(provider_name: str) -> AIProvider:
    """
    Factory function to get the appropriate AI provider.
    
    Args:
        provider_name: "openai" or "claude"
        
    Returns:
        Configured AIProvider instance
    """
    from app.config import get_settings
    settings = get_settings()
    
    if provider_name.lower() == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key)
    elif provider_name.lower() == "claude":
        return ClaudeProvider(api_key=settings.anthropic_api_key)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")


# =============================================================================
# Predefined Tools for JIRA/GitHub
# =============================================================================

# These tool definitions tell the AI what functions it can call
AVAILABLE_TOOLS = [
    ToolDefinition(
        name="get_jira_issues",
        description="Get JIRA issues assigned to a team member. Use this to find what tickets someone is working on.",
        parameters=[
            ToolParameter(
                name="username",
                type="string",
                description="The username of the team member (e.g., 'john', 'sarah')",
            )
        ],
    ),
    ToolDefinition(
        name="get_github_activity",
        description="Get recent GitHub activity for a team member including commits, pull requests, and active repositories.",
        parameters=[
            ToolParameter(
                name="username",
                type="string",
                description="The GitHub username of the team member",
            )
        ],
    ),
]
