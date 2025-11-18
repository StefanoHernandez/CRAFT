"""Example: Using CRAFT API as a client."""

import requests
import json


def chat_request_example():
    """Example of non-streaming chat request."""
    print("📤 Sending chat request...\n")

    response = requests.post(
        "http://localhost:8000/chat",
        json={
            "message": "What is CRAFT?",
            "use_rag": True,
            "save_history": True,
        },
        headers={
            # "Authorization": "Bearer your-api-key",  # If auth enabled
        },
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data['content']}")
        print(f"📊 Model: {data['model']}")
        print(f"💬 Conversation ID: {data['conversation_id']}")
        if data.get('usage'):
            print(f"🎯 Tokens: {data['usage']['total_tokens']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")


def streaming_request_example():
    """Example of streaming chat request."""
    print("\n" + "=" * 60)
    print("📤 Sending streaming request...\n")

    response = requests.post(
        "http://localhost:8000/chat/stream",
        json={
            "message": "Explain quantum computing in simple terms",
            "use_rag": True,
        },
        headers={
            # "Authorization": "Bearer your-api-key",
        },
        stream=True,
    )

    if response.status_code == 200:
        print("✅ Streaming response:\n")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        data = json.loads(data_str)
                        if data.get('content'):
                            print(data['content'], end='', flush=True)
                        if data.get('finished'):
                            print("\n\n✅ Streaming completed!")
                    except json.JSONDecodeError:
                        pass
    else:
        print(f"❌ Error: {response.status_code}")


def health_check_example():
    """Example of health check request."""
    print("\n" + "=" * 60)
    print("🏥 Checking API health...\n")

    response = requests.get("http://localhost:8000/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"📦 Version: {data['version']}")
        print(f"🤖 Provider: {data['provider']}")
        print(f"🧠 RAG Enabled: {data['rag_enabled']}")
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    print("🔌 CRAFT API Client Examples\n")
    print("Make sure the server is running: python examples/api_server.py\n")
    print("=" * 60)

    try:
        # Health check
        health_check_example()

        # Normal chat
        chat_request_example()

        # Streaming chat
        streaming_request_example()

    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server.")
        print("Please start the server first: python examples/api_server.py")


if __name__ == "__main__":
    main()
