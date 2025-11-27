"""Example: Running CRAFT API server."""

import os
from craft import Chatbot
from craft.providers import AnthropicProvider
from craft.integrations.api import CRAFTServer
from craft.integrations.api.auth import APIKeyManager
from craft.integrations.api.rate_limiter import RateLimiter


def main():
    print("🚀 CRAFT API Server Example\n")

    # Create chatbot
    chatbot = Chatbot(
        provider=AnthropicProvider(
            model="claude-sonnet-4.5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        ),
        system_prompt="You are a helpful AI assistant.",
        memory=True,
    )

    # Optional: Setup API key authentication
    api_key_manager = APIKeyManager()
    master_key = api_key_manager.create_key(
        name="admin",
        expires_in_days=365,
        rate_limit=100,  # 100 requests per minute
    )
    print(f"✅ Created API key: {master_key}\n")

    # Optional: Setup rate limiting
    rate_limiter = RateLimiter(requests_per_minute=60)

    # Create server
    server = CRAFTServer(
        chatbot=chatbot,
        title="My CRAFT API",
        description="Chatbot API powered by CRAFT",
        api_key_manager=api_key_manager,  # Remove for no auth
        rate_limiter=rate_limiter,
        enable_cors=True,
        cors_origins=["*"],  # Configure for production!
    )

    print("🌐 Server starting...")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("📍 Chat Endpoint: POST http://localhost:8000/chat")
    print("📍 WebSocket: ws://localhost:8000/ws")
    print("\n" + "=" * 60 + "\n")

    # Run server
    server.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
