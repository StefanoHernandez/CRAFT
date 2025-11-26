"""Beautiful trace formatting (Datapizza-style)."""

from typing import Optional
from craft.tracing.context import TraceContext, TraceSpan, SpanStatus


class TraceFormatter:
    """
    Format traces for beautiful console output.
    
    Inspired by Datapizza AI's clean, tree-style visualization.
    """
    
    # Icons for different operations
    ICONS = {
        "agent": "🤖",
        "tool": "🔧",
        "memory": "💾",
        "planning": "💭",
        "execution": "⚡",
        "synthesis": "🔄",
        "input": "📥",
        "output": "📤",
        "error": "❌",
        "success": "✅",
        "pending": "⏳",
    }
    
    # Colors (ANSI codes)
    COLORS = {
        "reset": "\033[0m",
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "gray": "\033[90m",
        "bold": "\033[1m",
    }
    
    def __init__(self, use_colors: bool = True, use_icons: bool = True):
        self.use_colors = use_colors
        self.use_icons = use_icons
    
    def format_trace(self, context: TraceContext) -> str:
        """
        Format a complete trace as a beautiful tree.
        
        Returns:
            Formatted string ready for console output
        """
        lines = []
        
        # Header
        duration_str = f"{context.duration:.2f}s"
        header = f"🔍 TRACE: {context.name} ({duration_str})"
        lines.append(self._colorize(header, "bold"))
        
        # Root span tree
        if context.root_span:
            lines.extend(self._format_span_tree(context.root_span, prefix="", is_last=True))
        
        # Summary
        summary = context.get_summary()
        lines.append("")
        lines.append(self._colorize("📋 Summary", "bold"))
        lines.append(f"   • Total Time: {summary['duration']:.2f}s")
        lines.append(f"   • Total Spans: {summary['total_spans']}")
        lines.append(f"   • Success: {self._colorize(str(summary['successful_spans']), 'green')}")
        lines.append(f"   • Errors: {self._colorize(str(summary['error_spans']), 'red')}")
        
        return "\n".join(lines)
    
    def _format_span_tree(
        self,
        span: TraceSpan,
        prefix: str = "",
        is_last: bool = True
    ) -> list:
        """Format a span and its children as a tree."""
        lines = []
        
        # Tree characters
        branch = "└─ " if is_last else "├─ "
        extension = "   " if is_last else "│  "
        
        # Icon for operation type
        icon = self._get_operation_icon(span.operation)
        
        # Status icon
        status_icon = self._get_status_icon(span.status)
        
        # Operation name
        op_name = span.operation.split(".")[-1] if "." in span.operation else span.operation
        op_name = op_name.capitalize()
        
        # Duration
        duration_str = f"({span.duration:.2f}s)" if span.end_time else "(running)"
        
        # Color based on status
        color = self._get_status_color(span.status)
        
        # Format line
        line = f"{prefix}{branch}{icon} {op_name} {duration_str} {status_icon}"
        lines.append(self._colorize(line, color))
        
        #  Add input/output details if present (for verbose mode)
        if span.inputs and len(span.children) == 0:
            input_str = span.inputs.get("query") if isinstance(span.inputs, dict) else str(span.inputs)
            if input_str:
                lines.append(self._colorize(f"{prefix}{extension}  📊 Input: {str(input_str)[:50]}...", "gray"))
        
        if span.outputs and span.status == SpanStatus.SUCCESS:
            output_keys = list(span.outputs.keys())
            lines.append(self._colorize(f"{prefix}{extension}  📊 Output: {output_keys}", "gray"))
        
        # Format children
        for i, child in enumerate(span.children):
            child_is_last = (i == len(span.children) - 1)
            lines.extend(
                self._format_span_tree(
                    child,
                    prefix=prefix + extension,
                    is_last=child_is_last
                )
            )
        
        return lines
    
    def _get_operation_icon(self, operation: str) -> str:
        """Get icon for operation type."""
        if not self.use_icons:
            return ""
        
        op_lower = operation.lower()
        for key, icon in self.ICONS.items():
            if key in op_lower:
                return icon
        
        return "•"
    
    def _get_status_icon(self, status: SpanStatus) -> str:
        """Get icon for status."""
        if not self.use_icons:
            return status.value
        
        if status == SpanStatus.SUCCESS:
            return self.ICONS["success"]
        elif status == SpanStatus.ERROR:
            return self.ICONS["error"]
        else:
            return self.ICONS["pending"]
    
    def _get_status_color(self, status: SpanStatus) -> str:
        """Get color for status."""
        if status == SpanStatus.SUCCESS:
            return "green"
        elif status == SpanStatus.ERROR:
            return "red"
        else:
            return "yellow"
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text."""
        if not self.use_colors:
            return text
        
        color_code = self.COLORS.get(color, "")
        reset = self.COLORS["reset"]
        
        if color_code:
            return f"{color_code}{text}{reset}"
        return text
