"""Error classes for CRAFT."""

from typing import Any, Dict, Optional


class CRAFTError(Exception):
    """Base exception for CRAFT errors."""

    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        recovery_suggestion: Optional[str] = None
    ):
        """
        Initialize CRAFT error.

        Args:
            message: Error message
            details: Optional dictionary with error details
            recovery_suggestion: Optional suggestion for recovering from the error
        """
        self.message = message
        self.details = details or {}
        self.recovery_suggestion = recovery_suggestion
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of error."""
        parts = [self.message]
        
        if self.recovery_suggestion:
            parts.append(f"Suggestion: {self.recovery_suggestion}")
            
        if self.details:
            details_str = "\n".join(f"  {k}: {v}" for k, v in self.details.items())
            parts.append(f"Details:\n{details_str}")
            
        return "\n".join(parts)


class ToolExecutionError(CRAFTError):
    """Tool execution failed."""

    def __init__(
        self,
        tool_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
        recovery_suggestion: Optional[str] = None,
    ):
        """
        Initialize tool execution error.

        Args:
            tool_name: Name of the tool that failed
            message: Error message
            details: Optional error details
            original_exception: Original exception if any
            recovery_suggestion: Optional recovery suggestion
        """
        self.tool_name = tool_name
        self.original_exception = original_exception

        # Add tool name and exception to details
        error_details = details or {}
        error_details["tool_name"] = tool_name
        if original_exception:
            error_details["exception_type"] = type(original_exception).__name__
            error_details["exception_message"] = str(original_exception)

        super().__init__(message, error_details, recovery_suggestion)


class ToolValidationError(ToolExecutionError):
    """Tool parameter validation failed."""

    def __init__(
        self,
        tool_name: str,
        validation_errors: list[str],
        provided_args: Dict[str, Any],
    ):
        """
        Initialize tool validation error.

        Args:
            tool_name: Name of the tool
            validation_errors: List of validation error messages
            provided_args: Arguments that were provided
        """
        message = f"Tool '{tool_name}' parameter validation failed"
        details = {
            "validation_errors": validation_errors,
            "provided_arguments": list(provided_args.keys()),
        }
        suggestion = f"Check the arguments for '{tool_name}' against its schema. Errors: {', '.join(validation_errors)}"
        super().__init__(tool_name, message, details, recovery_suggestion=suggestion)


class AgentExecutionError(CRAFTError):
    """Agent execution failed."""

    pass


class ProviderError(CRAFTError):
    """Provider API error."""

    def __init__(
        self,
        provider_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        recovery_suggestion: Optional[str] = None,
    ):
        """
        Initialize provider error.

        Args:
            provider_name: Name of the provider
            message: Error message
            details: Optional error details
            retryable: Whether the error is retryable
            recovery_suggestion: Optional recovery suggestion
        """
        self.provider_name = provider_name
        self.retryable = retryable

        error_details = details or {}
        error_details["provider"] = provider_name
        error_details["retryable"] = retryable

        super().__init__(message, error_details, recovery_suggestion)


class MCPError(CRAFTError):
    """MCP protocol error."""

    pass


class RAGError(CRAFTError):
    """RAG system error."""

    pass
