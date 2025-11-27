"""
Examples for new LLM providers: Azure OpenAI, AWS Bedrock, Cohere

This demonstrates the new providers added in CRAFT v1.4.0
"""

import os
from craft.chatbot import Chatbot
from craft.providers.base import Message, Role


def example_1_azure_openai_basic():
    """Example 1: Basic Azure OpenAI usage"""
    print("\n=== Example 1: Azure OpenAI Basic ===\n")

    # Setup Azure OpenAI
    chatbot = Chatbot(
        provider="azure_openai",
        model="gpt-4o",  # Your Azure deployment name
        azure_endpoint="https://your-resource.openai.azure.com/",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview"
    )

    response = chatbot.chat("Explain Azure OpenAI in one sentence.")
    print(f"Response: {response}")
    print(f"Tokens: {chatbot.get_usage()}")


def example_2_azure_openai_streaming():
    """Example 2: Azure OpenAI with streaming"""
    print("\n=== Example 2: Azure OpenAI Streaming ===\n")

    chatbot = Chatbot(
        provider="azure_openai",
        model="gpt-4-deployment",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )

    print("Streaming response:")
    for chunk in chatbot.stream("Write a haiku about cloud computing"):
        print(chunk, end="", flush=True)
    print("\n")


def example_3_aws_bedrock_claude():
    """Example 3: AWS Bedrock with Claude"""
    print("\n=== Example 3: AWS Bedrock Claude ===\n")

    # AWS Bedrock with Claude 3 Sonnet
    chatbot = Chatbot(
        provider="aws_bedrock",
        model="anthropic.claude-sonnet-4.5-20240229-v1:0",
        region_name="us-east-1",
        # AWS credentials from environment or IAM role
    )

    response = chatbot.chat("What is AWS Bedrock? Answer briefly.")
    print(f"Response: {response}")


def example_4_aws_bedrock_titan():
    """Example 4: AWS Bedrock with Amazon Titan"""
    print("\n=== Example 4: AWS Bedrock Titan ===\n")

    chatbot = Chatbot(
        provider="aws_bedrock",
        model="amazon.titan-text-express-v1",
        region_name="us-west-2"
    )

    response = chatbot.chat("Explain Amazon Titan models.")
    print(f"Response: {response}")


def example_5_aws_bedrock_conversation():
    """Example 5: AWS Bedrock conversation with context"""
    print("\n=== Example 5: AWS Bedrock Conversation ===\n")

    chatbot = Chatbot(
        provider="aws_bedrock",
        model="anthropic.claude-sonnet-4.5-20240229-v1:0",
        region_name="us-east-1"
    )

    # Multi-turn conversation
    response1 = chatbot.chat("My name is Alice and I like coding.")
    print(f"Bot: {response1}")

    response2 = chatbot.chat("What's my name and what do I like?")
    print(f"Bot: {response2}")

    print(f"\nConversation history: {len(chatbot.get_conversation())} messages")


def example_6_cohere_basic():
    """Example 6: Basic Cohere usage"""
    print("\n=== Example 6: Cohere Basic ===\n")

    chatbot = Chatbot(
        provider="cohere",
        model="command",
        api_key=os.getenv("COHERE_API_KEY")
    )

    response = chatbot.chat("What is Cohere? Answer in one sentence.")
    print(f"Response: {response}")


def example_7_cohere_with_documents():
    """Example 7: Cohere with RAG documents"""
    print("\n=== Example 7: Cohere with Documents ===\n")

    chatbot = Chatbot(
        provider="cohere",
        model="command-r",  # RAG-optimized model
        api_key=os.getenv("COHERE_API_KEY")
    )

    # Cohere supports passing documents for RAG
    documents = [
        {"text": "CRAFT is a chatbot and RAG framework for Python."},
        {"text": "CRAFT supports multiple LLM providers including OpenAI, Anthropic, and Cohere."},
        {"text": "CRAFT v1.4.0 introduces advanced RAG features."}
    ]

    from craft.providers.cohere import CohereProvider
    from craft.providers.base import Message, Role

    # Using provider directly for RAG features
    provider = CohereProvider(
        model="command-r",
        api_key=os.getenv("COHERE_API_KEY")
    )

    response = provider.chat(
        messages=[Message(role=Role.USER, content="What is CRAFT?")],
        documents=documents
    )

    print(f"Response: {response.content}")
    print(f"Citations: {response.metadata.get('citations', 'None')}")


def example_8_cohere_streaming():
    """Example 8: Cohere streaming"""
    print("\n=== Example 8: Cohere Streaming ===\n")

    chatbot = Chatbot(
        provider="cohere",
        model="command-light",  # Faster model
        api_key=os.getenv("COHERE_API_KEY")
    )

    print("Streaming response:")
    for chunk in chatbot.stream("Write a creative tagline for CRAFT framework"):
        print(chunk, end="", flush=True)
    print("\n")


def example_9_provider_switching():
    """Example 9: Easy provider switching"""
    print("\n=== Example 9: Provider Switching ===\n")

    providers = [
        ("openai", "gpt-4o"),
        ("azure_openai", "gpt-4o"),
        ("aws_bedrock", "anthropic.claude-sonnet-4.5-20240229-v1:0"),
        ("cohere", "command")
    ]

    query = "What is 2+2? Answer with just the number."

    for provider_name, model in providers:
        try:
            if provider_name == "azure_openai":
                chatbot = Chatbot(
                    provider=provider_name,
                    model=model,
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_API_KEY")
                )
            else:
                chatbot = Chatbot(provider=provider_name, model=model)

            response = chatbot.chat(query)
            print(f"{provider_name}: {response}")

        except Exception as e:
            print(f"{provider_name}: Skipped ({str(e)[:50]}...)")


def example_10_compare_models():
    """Example 10: Compare different models on same task"""
    print("\n=== Example 10: Model Comparison ===\n")

    task = "Translate 'Hello, world!' to French, Spanish, and German."

    models = [
        ("openai", "gpt-3.5-turbo"),
        ("aws_bedrock", "anthropic.claude-haiku-4.5-20240307-v1:0"),
        ("cohere", "command-light")
    ]

    for provider, model in models:
        try:
            chatbot = Chatbot(provider=provider, model=model)
            response = chatbot.chat(task)
            print(f"\n{provider} ({model}):")
            print(response)

        except Exception as e:
            print(f"\n{provider}: Error - {str(e)[:100]}")


if __name__ == "__main__":
    print("CRAFT v1.4.0 - New Provider Examples")
    print("=" * 50)

    # Run examples
    examples = [
        example_1_azure_openai_basic,
        example_2_azure_openai_streaming,
        example_3_aws_bedrock_claude,
        example_4_aws_bedrock_titan,
        example_5_aws_bedrock_conversation,
        example_6_cohere_basic,
        example_7_cohere_with_documents,
        example_8_cohere_streaming,
        example_9_provider_switching,
        example_10_compare_models,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample skipped: {str(e)[:100]}")

    print("\n" + "=" * 50)
    print("Examples completed!")
