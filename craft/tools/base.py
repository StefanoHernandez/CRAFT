"""Base classes for the tool system."""

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import traceback

from craft.core.errors import ToolExecutionError, ToolValidationError

try:
    from toon import encode as toon_encode, decode as toon_decode
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False


class ToolParameter(BaseModel):
    """Parameter definition for a tool."""

    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolMetadata(BaseModel):
    """Metadata for a tool."""

    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str
    json_schema: Dict[str, Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Tool(BaseModel):
    """Base tool class representing a callable function."""

    name: str
    description: str
    func: Callable
    metadata: ToolMetadata

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __call__(self, **kwargs) -> Any:
        """
        Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            ToolValidationError: If argument validation fails
            ToolExecutionError: If tool execution fails
        """
        from craft.tracing import tracer
        
        with tracer.span(f"tool.{self.name}", tool=self.name, inputs=kwargs) as span:
            try:
                # Validate arguments before execution
                validated_args = self.validate_args(**kwargs)
            except ValueError as e:
                # Convert validation errors to ToolValidationError
                raise ToolValidationError(
                    tool_name=self.name,
                    validation_errors=[str(e)],
                    provided_args=kwargs,
                )
            
            try:
                # Execute the tool
                result = self.func(**validated_args)
                
                # Capture result in span (truncated if too long)
                result_str = str(result)
                if len(result_str) > 500:
                    result_str = result_str[:500] + "..."
                span.set_output(result=result_str)
                
                return result
            except Exception as e:
                # Capture execution error with full context
                error_details = {
                    "arguments": validated_args,
                    "stack_trace": traceback.format_exc(),
                }
                raise ToolExecutionError(
                    tool_name=self.name,
                    message=f"Tool execution failed: {str(e)}",
                    details=error_details,
                    original_exception=e,
                )

    def validate_args(self, **kwargs) -> Dict[str, Any]:
        """
        Validate arguments against the tool's parameter schema.

        Args:
            **kwargs: Arguments to validate

        Returns:
            Validated arguments dictionary

        Raises:
            ValueError: If validation fails with detailed error messages
        """
        validated = {}
        errors = []

        # Check required parameters
        for param in self.metadata.parameters:
            if param.required and param.name not in kwargs:
                errors.append(
                    f"Missing required parameter '{param.name}' of type {param.type}"
                )
            elif param.name in kwargs:
                # Validate type
                value = kwargs[param.name]
                type_valid, type_error = self._validate_type(value, param.type, param.name)
                if not type_valid:
                    errors.append(type_error)
                else:
                    validated[param.name] = value
            elif param.default is not None:
                validated[param.name] = param.default

        # Check for unexpected parameters
        expected_params = {p.name for p in self.metadata.parameters}
        for key in kwargs:
            if key not in expected_params:
                errors.append(f"Unexpected parameter '{key}'")

        if errors:
            error_msg = "Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            error_msg += f"\n\nExpected parameters: {', '.join(expected_params)}"
            error_msg += f"\n\nSuggestion: Check parameter names and types. "
            error_msg += f"Use {self.name}() with parameters: "
            error_msg += ", ".join(
                f"{p.name}: {p.type}" + ("" if p.required else " (optional)")
                for p in self.metadata.parameters
            )
            raise ValueError(error_msg)

        return validated
    
    def _validate_type(self, value: Any, expected_type: str, param_name: str) -> tuple[bool, str]:
        """
        Validate that a value matches the expected type.
        
        Args:
            value: Value to validate
            expected_type: Expected type as string
            param_name: Parameter name for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Type mapping
        type_checks = {
            "str": (str, "string"),
            "string": (str, "string"),
            "int": (int, "integer"),
            "integer": (int, "integer"),
            "float": (float, "number"),
            "number": ((int, float), "number"),
            "bool": (bool, "boolean"),
            "boolean": (bool, "boolean"),
            "list": (list, "array"),
            "array": (list, "array"),
            "dict": (dict, "object"),
            "object": (dict, "object"),
        }
        
        # Normalize type string
        type_lower = expected_type.lower()
        
        # Check if we have a type check for this
        if type_lower in type_checks:
            expected_python_type, type_name = type_checks[type_lower]
            if not isinstance(value, expected_python_type):
                actual_type = type(value).__name__
                return False, (
                    f"Parameter '{param_name}' has invalid type. "
                    f"Expected {type_name}, got {actual_type}"
                )
        
        # Type is valid or unknown (we allow unknown types)
        return True, ""

    def to_function_schema(self, format: str = "json") -> Dict[str, Any]:
        """
        Convert tool to function schema format for LLM providers.
        
        Args:
            format: Output format - "json" (default) or "toon"
            
        Returns:
            Function schema dictionary
        """
        if format == "toon" and TOON_AVAILABLE:
            # Return TOON-optimized schema
            return self._to_toon_schema()
        return self.metadata.json_schema
    
    def _to_toon_schema(self) -> Dict[str, Any]:
        """
        Generate TOON-optimized schema for the tool.
        
        TOON format reduces token usage by 30-60% compared to JSON.
        """
        # Convert parameters to TOON-friendly format
        params_list = []
        for param in self.metadata.parameters:
            param_info = {
                "name": param.name,
                "type": param.type,
                "required": param.required
            }
            if param.description:
                param_info["desc"] = param.description
            if param.default is not None:
                param_info["default"] = param.default
            params_list.append(param_info)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "format": "toon",  # Signal that TOON format is preferred
                    "schema": params_list
                }
            }
        }
