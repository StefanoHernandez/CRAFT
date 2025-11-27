"""AWS Bedrock provider implementation."""

import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union

try:
    import boto3
    from botocore.config import Config
    AWS_BEDROCK_AVAILABLE = True
except ImportError:
    AWS_BEDROCK_AVAILABLE = False

from pydantic import Field
from craft.providers.base import (
    Provider,
    ProviderConfig,
    Message,
    ChatResponse,
    StreamChunk,
    Role,
)


class AWSBedrockConfig(ProviderConfig):
    """AWS Bedrock-specific configuration."""

    model: str = Field(default="anthropic.claude-sonnet-4.5-20240229-v1:0")
    aws_access_key_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID")
    )
    aws_secret_access_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    aws_session_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_SESSION_TOKEN")
    )
    region_name: str = Field(default="us-east-1")
    max_tokens: int = Field(default=4096)


class AWSBedrockProvider(Provider):
    """
    AWS Bedrock provider implementation.

    Supports Claude, Titan, Jurassic, and other models via AWS Bedrock.

    Supported model families:
    - Anthropic Claude: anthropic.claude-3-* (Opus, Sonnet, Haiku)
    - Amazon Titan: amazon.titan-*
    - AI21 Jurassic: ai21.j2-*
    - Cohere Command: cohere.command-*
    - Meta Llama: meta.llama2-*

    Example:
        >>> from craft.providers import AWSBedrockProvider, Message, Role
        >>>
        >>> config = AWSBedrockConfig(
        ...     model="anthropic.claude-sonnet-4.5-20240229-v1:0",
        ...     region_name="us-east-1"
        ... )
        >>> provider = AWSBedrockProvider(config)
        >>>
        >>> response = provider.chat([
        ...     Message(role=Role.USER, content="Hello!")
        ... ])
        >>> print(response.content)
    """

    # Model family detection patterns
    MODEL_FAMILIES = {
        "anthropic": ["anthropic.claude"],
        "amazon": ["amazon.titan"],
        "ai21": ["ai21.j2"],
        "cohere": ["cohere.command"],
        "meta": ["meta.llama"],
    }

    def __init__(self, config: Optional[AWSBedrockConfig] = None, **kwargs: Any):
        """
        Initialize AWS Bedrock provider.

        Args:
            config: AWS Bedrock configuration
            **kwargs: Additional config parameters

        Environment Variables:
            AWS_ACCESS_KEY_ID: AWS access key
            AWS_SECRET_ACCESS_KEY: AWS secret key
            AWS_SESSION_TOKEN: AWS session token (optional)
            AWS_REGION: AWS region (default: us-east-1)
        """
        if not AWS_BEDROCK_AVAILABLE:
            raise ImportError(
                "boto3 package not installed. "
                "Install with: pip install 'craft-chatbot[aws]'"
            )

        if config is None:
            config = AWSBedrockConfig(**kwargs)
        elif kwargs:
            config = AWSBedrockConfig(**{**config.model_dump(), **kwargs})

        super().__init__(config)

        # Configure boto3 client
        boto_config = Config(
            region_name=self.config.region_name,
            read_timeout=self.config.timeout,
            retries={"max_attempts": self.config.max_retries},
        )

        session_kwargs = {}
        if self.config.aws_access_key_id:
            session_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
        if self.config.aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = self.config.aws_secret_access_key
        if self.config.aws_session_token:
            session_kwargs["aws_session_token"] = self.config.aws_session_token

        self.client = boto3.client(
            "bedrock-runtime",
            config=boto_config,
            **session_kwargs
        )

        # Detect model family
        self.model_family = self._detect_model_family()

    def _detect_model_family(self) -> str:
        """Detect which model family is being used."""
        model_id = self.config.model.lower()
        for family, patterns in self.MODEL_FAMILIES.items():
            if any(pattern in model_id for pattern in patterns):
                return family
        return "unknown"

    def _validate_config(self) -> None:
        """Validate AWS Bedrock configuration."""
        # AWS credentials are optional if using IAM role
        if self.model_family == "unknown":
            # Warn but don't fail - might still work
            pass

    def chat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Send chat request to AWS Bedrock.

        Args:
            messages: List of conversation messages
            stream: Whether to stream the response
            **kwargs: Additional Bedrock-specific parameters

        Returns:
            ChatResponse or iterator of StreamChunk if streaming
        """
        # Build request body based on model family
        body = self._build_request_body(messages, **kwargs)

        if stream:
            return self._stream(body)
        else:
            return self._complete(body)

    def _build_request_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for specific model family."""
        if self.model_family == "anthropic":
            return self._build_anthropic_body(messages, **kwargs)
        elif self.model_family == "amazon":
            return self._build_titan_body(messages, **kwargs)
        elif self.model_family == "ai21":
            return self._build_ai21_body(messages, **kwargs)
        elif self.model_family == "cohere":
            return self._build_cohere_body(messages, **kwargs)
        elif self.model_family == "meta":
            return self._build_meta_body(messages, **kwargs)
        else:
            # Generic fallback
            return self._build_generic_body(messages, **kwargs)

    def _build_anthropic_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for Anthropic Claude models."""
        # Separate system message from conversation
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": conversation_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        if system_message:
            body["system"] = system_message

        return body

    def _build_titan_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for Amazon Titan models."""
        # Titan uses a simpler format
        prompt = "\n".join([f"{msg.role.value}: {msg.content}" for msg in messages])

        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "topP": kwargs.get("top_p", self.config.top_p),
            }
        }

    def _build_ai21_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for AI21 Jurassic models."""
        prompt = "\n".join([f"{msg.role.value}: {msg.content}" for msg in messages])

        return {
            "prompt": prompt,
            "maxTokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "topP": kwargs.get("top_p", self.config.top_p),
        }

    def _build_cohere_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for Cohere Command models."""
        # Cohere separates message and chat_history
        message = messages[-1].content if messages else ""
        chat_history = [
            {"role": msg.role.value, "message": msg.content}
            for msg in messages[:-1]
        ]

        return {
            "message": message,
            "chat_history": chat_history,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "p": kwargs.get("top_p", self.config.top_p),
        }

    def _build_meta_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Build request body for Meta Llama models."""
        prompt = "\n".join([f"{msg.role.value}: {msg.content}" for msg in messages])

        return {
            "prompt": prompt,
            "max_gen_len": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

    def _build_generic_body(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Generic fallback body builder."""
        return {
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in messages],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

    def _complete(self, body: Dict[str, Any]) -> ChatResponse:
        """Complete (non-streaming) request."""
        response = self.client.invoke_model(
            modelId=self.config.model,
            body=json.dumps(body)
        )

        response_body = json.loads(response["body"].read())

        # Parse response based on model family
        content, usage = self._parse_response(response_body)

        return ChatResponse(
            content=content,
            role=Role.ASSISTANT,
            model=self.config.model,
            usage=usage,
            metadata={
                "provider": "aws_bedrock",
                "model_family": self.model_family,
                "request_id": response.get("ResponseMetadata", {}).get("RequestId"),
            },
        )

    def _parse_response(self, response_body: Dict[str, Any]) -> tuple[str, Dict[str, int]]:
        """Parse response based on model family."""
        if self.model_family == "anthropic":
            content = response_body.get("content", [{}])[0].get("text", "")
            usage = {
                "prompt_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_body.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    response_body.get("usage", {}).get("input_tokens", 0) +
                    response_body.get("usage", {}).get("output_tokens", 0)
                ),
            }
        elif self.model_family == "amazon":
            content = response_body.get("results", [{}])[0].get("outputText", "")
            usage = {
                "prompt_tokens": response_body.get("inputTextTokenCount", 0),
                "completion_tokens": response_body.get("results", [{}])[0].get("tokenCount", 0),
                "total_tokens": 0,  # Titan doesn't provide total
            }
        elif self.model_family == "ai21":
            content = response_body.get("completions", [{}])[0].get("data", {}).get("text", "")
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        elif self.model_family == "cohere":
            content = response_body.get("text", "")
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        elif self.model_family == "meta":
            content = response_body.get("generation", "")
            usage = {
                "prompt_tokens": response_body.get("prompt_token_count", 0),
                "completion_tokens": response_body.get("generation_token_count", 0),
                "total_tokens": 0,
            }
        else:
            # Generic fallback
            content = str(response_body)
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        return content, usage

    def _stream(self, body: Dict[str, Any]) -> AsyncIterator[StreamChunk]:
        """Streaming request."""
        response = self.client.invoke_model_with_response_stream(
            modelId=self.config.model,
            body=json.dumps(body)
        )

        for event in response.get("body"):
            chunk = json.loads(event["chunk"]["bytes"])

            # Parse chunk based on model family
            content = self._parse_stream_chunk(chunk)
            if content:
                yield StreamChunk(content=content)

        yield StreamChunk(content="", finished=True)

    def _parse_stream_chunk(self, chunk: Dict[str, Any]) -> str:
        """Parse streaming chunk based on model family."""
        if self.model_family == "anthropic":
            if chunk.get("type") == "content_block_delta":
                return chunk.get("delta", {}).get("text", "")
        elif self.model_family == "amazon":
            return chunk.get("outputText", "")
        elif self.model_family == "cohere":
            return chunk.get("text", "")
        # Add other model families as needed
        return ""

    async def achat(
        self,
        messages: List[Message],
        stream: bool = False,
        **kwargs: Any,
    ) -> Union[ChatResponse, AsyncIterator[StreamChunk]]:
        """
        Async chat request to AWS Bedrock.

        Note: boto3 doesn't have native async support, so this uses sync client.
        For true async, consider using aioboto3.
        """
        # For now, delegate to sync version
        # TODO: Implement with aioboto3 for true async
        return self.chat(messages, stream, **kwargs)


__all__ = ["AWSBedrockProvider", "AWSBedrockConfig", "AWS_BEDROCK_AVAILABLE"]
