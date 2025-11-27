
import os
from unittest.mock import MagicMock, patch
from craft.providers import HuggingFaceProvider, TogetherAIProvider, ReplicateProvider
from craft.core.conversation import Message
from craft.providers.base import Role

def test_huggingface():
    print("\n--- Testing HuggingFaceProvider ---")
    with patch("craft.providers.huggingface.InferenceClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat_completion.return_value.choices[0].message.content = "Hello from HF!"
        
        provider = HuggingFaceProvider(api_key="mock_key")
        response = provider.chat([Message(role=Role.USER, content="Hi")])
        print(f"Response: {response.content}")
        assert response.content == "Hello from HF!"

def test_together():
    print("\n--- Testing TogetherAIProvider ---")
    with patch("craft.providers.together.together") as mock_together:
        mock_client = mock_together.Together.return_value
        mock_client.chat.completions.create.return_value.choices[0].message.content = "Hello from Together!"
        
        provider = TogetherAIProvider(api_key="mock_key")
        response = provider.chat([Message(role=Role.USER, content="Hi")])
        print(f"Response: {response.content}")
        assert response.content == "Hello from Together!"

def test_replicate():
    print("\n--- Testing ReplicateProvider ---")
    with patch("craft.providers.replicate.replicate") as mock_replicate:
        mock_client = mock_replicate.Client.return_value
        # Mock run to return iterator of strings
        mock_client.run.return_value = iter(["Hello ", "from ", "Replicate!"])
        
        provider = ReplicateProvider(api_key="mock_key")
        response = provider.chat([Message(role=Role.USER, content="Hi")])
        print(f"Response: {response.content}")
        assert response.content == "Hello from Replicate!"

if __name__ == "__main__":
    test_huggingface()
    test_together()
    test_replicate()
    print("\n✅ All Enterprise Providers verified (mocked)!")
