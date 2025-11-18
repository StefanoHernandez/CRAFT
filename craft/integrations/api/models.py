"""API request/response models."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID to continue")
    stream: bool = Field(default=False, description="Enable streaming response")
    use_rag: bool = Field(default=True, description="Use RAG if available")
    save_history: bool = Field(default=True, description="Save to conversation history")
    provider_params: Dict[str, Any] = Field(default_factory=dict, description="Additional provider parameters")


class StreamChatRequest(BaseModel):
    """Streaming chat request model."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID to continue")
    use_rag: bool = Field(default=True, description="Use RAG if available")
    save_history: bool = Field(default=True, description="Save to conversation history")


class ChatResponse(BaseModel):
    """Chat response model."""

    content: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class StreamChunkResponse(BaseModel):
    """Streaming chunk response model."""

    content: str = Field(..., description="Chunk content")
    finished: bool = Field(default=False, description="Whether streaming is finished")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")


class ConversationResponse(BaseModel):
    """Conversation response model."""

    id: str = Field(..., description="Conversation ID")
    message_count: int = Field(..., description="Number of messages")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Conversation metadata")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="CRAFT version")
    provider: str = Field(..., description="Active LLM provider")
    rag_enabled: bool = Field(..., description="RAG availability")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
