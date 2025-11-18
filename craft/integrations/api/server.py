"""FastAPI server for CRAFT chatbot."""

import json
from typing import Optional
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

import craft
from craft.core.chatbot import Chatbot
from craft.providers.base import Provider
from craft.integrations.api.models import (
    ChatRequest,
    ChatResponse,
    StreamChatRequest,
    StreamChunkResponse,
    ConversationResponse,
    HealthResponse,
    ErrorResponse,
)
from craft.integrations.api.auth import APIKeyManager, verify_api_key
from craft.integrations.api.rate_limiter import RateLimiter
from craft.utils.logging import get_logger


class CRAFTServer:
    """
    FastAPI server for CRAFT chatbot.

    Provides REST API and WebSocket endpoints for easy integration.
    """

    def __init__(
        self,
        chatbot: Chatbot,
        title: str = "CRAFT API",
        description: str = "Chatbot & RAG Framework Toolkit API",
        version: str = craft.__version__,
        api_key_manager: Optional[APIKeyManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        enable_cors: bool = True,
        cors_origins: list[str] = ["*"],
    ):
        """
        Initialize CRAFT server.

        Args:
            chatbot: CRAFT Chatbot instance
            title: API title
            description: API description
            version: API version
            api_key_manager: Optional API key manager for authentication
            rate_limiter: Optional rate limiter
            enable_cors: Enable CORS middleware
            cors_origins: Allowed CORS origins
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "fastapi not installed. Install with: pip install 'craft-chatbot[api]'"
            )

        self.chatbot = chatbot
        self.api_key_manager = api_key_manager
        self.rate_limiter = rate_limiter or RateLimiter(requests_per_minute=60)
        self.logger = get_logger("craft.api")

        # Create FastAPI app
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
        )

        # Add CORS middleware
        if enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Register routes
        self._register_routes()

    def _get_api_key(self) -> Optional[str]:
        """Get API key from dependency injection."""
        if self.api_key_manager:
            return Depends(lambda creds=Depends(verify_api_key): verify_api_key(creds, self.api_key_manager))
        return None

    def _check_rate_limit(self, api_key: str) -> None:
        """Check rate limit for API key."""
        if not self.rate_limiter.check_rate_limit(api_key):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.get("/", response_model=HealthResponse)
        async def root():
            """Root endpoint with service info."""
            return {
                "status": "running",
                "version": craft.__version__,
                "provider": self.chatbot.provider.name,
                "rag_enabled": self.chatbot.rag is not None,
            }

        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "version": craft.__version__,
                "provider": self.chatbot.provider.name,
                "rag_enabled": self.chatbot.rag is not None,
            }

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(
            request: ChatRequest,
            api_key: str = Depends(self._get_api_key) if self.api_key_manager else None,
        ):
            """
            Chat endpoint for non-streaming responses.

            Args:
                request: Chat request with message and options

            Returns:
                Chat response with assistant message
            """
            try:
                # Rate limiting
                if api_key:
                    self._check_rate_limit(api_key)

                # Load conversation if ID provided
                if request.conversation_id:
                    self.chatbot.load_conversation(request.conversation_id)

                # Get response
                response = await self.chatbot.achat(
                    message=request.message,
                    stream=False,
                    save_history=request.save_history,
                    use_rag=request.use_rag,
                    **request.provider_params,
                )

                return ChatResponse(
                    content=response.content,
                    conversation_id=self.chatbot.conversation_id,
                    model=response.model,
                    usage=response.usage,
                    metadata=response.metadata,
                )

            except Exception as e:
                self.logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/chat/stream")
        async def chat_stream(
            request: StreamChatRequest,
            api_key: str = Depends(self._get_api_key) if self.api_key_manager else None,
        ):
            """
            Streaming chat endpoint using Server-Sent Events.

            Args:
                request: Streaming chat request

            Returns:
                StreamingResponse with SSE
            """
            try:
                # Rate limiting
                if api_key:
                    self._check_rate_limit(api_key)

                # Load conversation if ID provided
                if request.conversation_id:
                    self.chatbot.load_conversation(request.conversation_id)

                async def event_generator():
                    """Generate SSE events."""
                    try:
                        stream = await self.chatbot.achat(
                            message=request.message,
                            stream=True,
                            save_history=request.save_history,
                            use_rag=request.use_rag,
                        )

                        async for chunk in stream:
                            chunk_data = StreamChunkResponse(
                                content=chunk.content,
                                finished=chunk.finished,
                                conversation_id=self.chatbot.conversation_id if chunk.finished else None,
                            )
                            yield f"data: {chunk_data.model_dump_json()}\n\n"

                    except Exception as e:
                        error_data = {"error": str(e)}
                        yield f"data: {json.dumps(error_data)}\n\n"

                return StreamingResponse(
                    event_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            except Exception as e:
                self.logger.error(f"Streaming error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """
            WebSocket endpoint for real-time chat.

            Protocol:
            - Client sends JSON: {"message": "...", "use_rag": true}
            - Server sends JSON chunks: {"content": "...", "finished": false}
            """
            await websocket.accept()
            self.logger.info("WebSocket connection established")

            try:
                while True:
                    # Receive message
                    data = await websocket.receive_json()
                    message = data.get("message")
                    use_rag = data.get("use_rag", True)

                    if not message:
                        await websocket.send_json({"error": "Message is required"})
                        continue

                    # Get streaming response
                    stream = await self.chatbot.achat(
                        message=message,
                        stream=True,
                        use_rag=use_rag,
                    )

                    # Send chunks
                    async for chunk in stream:
                        await websocket.send_json({
                            "content": chunk.content,
                            "finished": chunk.finished,
                        })

            except WebSocketDisconnect:
                self.logger.info("WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await websocket.send_json({"error": str(e)})
                await websocket.close()

        @self.app.get("/conversation/{conversation_id}", response_model=ConversationResponse)
        async def get_conversation(
            conversation_id: str,
            api_key: str = Depends(self._get_api_key) if self.api_key_manager else None,
        ):
            """Get conversation details."""
            if not self.chatbot.memory:
                raise HTTPException(
                    status_code=400,
                    detail="Memory not enabled"
                )

            conversation = self.chatbot.memory.load(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )

            return ConversationResponse(
                id=conversation.id,
                message_count=len(conversation.messages),
                created_at=conversation.created_at.isoformat(),
                updated_at=conversation.updated_at.isoformat(),
                metadata=conversation.metadata,
            )

        @self.app.delete("/conversation/{conversation_id}")
        async def delete_conversation(
            conversation_id: str,
            api_key: str = Depends(self._get_api_key) if self.api_key_manager else None,
        ):
            """Delete a conversation."""
            if not self.chatbot.memory:
                raise HTTPException(
                    status_code=400,
                    detail="Memory not enabled"
                )

            success = self.chatbot.memory.delete(conversation_id)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found"
                )

            return {"status": "deleted", "conversation_id": conversation_id}

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """
        Run the server using uvicorn.

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn parameters
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError(
                "uvicorn not installed. Install with: pip install 'craft-chatbot[api]'"
            )

        self.logger.info(f"Starting CRAFT server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)
