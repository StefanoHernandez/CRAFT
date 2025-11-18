"""Advanced logging system."""

from enum import Enum
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AdvancedLogger:
    """
    Advanced structured logging with JSON output support.

    Provides structured logging with context, metrics, and JSON formatting.

    Examples:
        logger = AdvancedLogger("my-app")

        # Basic logging
        logger.info("User logged in", user_id="123")

        # With context
        logger.with_context(request_id="abc").info("Processing request")

        # JSON logging
        logger = AdvancedLogger("my-app", json_logs=True)
        logger.info("Event", data={"key": "value"})
    """

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        json_logs: bool = False,
        log_file: Optional[str] = None,
    ):
        """
        Initialize advanced logger.

        Args:
            name: Logger name
            level: Log level
            json_logs: Output logs as JSON
            log_file: Optional log file path
        """
        self.name = name
        self.json_logs = json_logs
        self._context: Dict[str, Any] = {}

        # Setup standard logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.value))

        if json_logs:
            console_handler.setFormatter(JSONFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.value))

            if json_logs:
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

    def with_context(self, **context) -> "AdvancedLogger":
        """
        Add context to logger (returns new instance).

        Args:
            **context: Context key-value pairs

        Returns:
            New logger instance with context
        """
        new_logger = AdvancedLogger.__new__(AdvancedLogger)
        new_logger.name = self.name
        new_logger.json_logs = self.json_logs
        new_logger.logger = self.logger
        new_logger._context = {**self._context, **context}
        return new_logger

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Internal log method."""
        if self.json_logs:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": level.value,
                "message": message,
                "logger": self.name,
                **self._context,
                **kwargs,
            }
            getattr(self.logger, level.value.lower())(json.dumps(log_data))
        else:
            extra_info = ""
            if self._context or kwargs:
                combined = {**self._context, **kwargs}
                extra_info = " " + " ".join(f"{k}={v}" for k, v in combined.items())

            getattr(self.logger, level.value.lower())(f"{message}{extra_info}")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs) -> None:
        """
        Log exception with traceback.

        Args:
            message: Log message
            exc: Optional exception
            **kwargs: Additional context
        """
        if exc:
            kwargs["exception"] = str(exc)
            kwargs["exception_type"] = type(exc).__name__

        self.logger.exception(message, extra=kwargs)


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in [
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "message", "pathname", "process", "processName",
                    "relativeCreated", "thread", "threadName", "exc_info",
                    "exc_text", "stack_info"
                ]:
                    log_data[key] = value

        return json.dumps(log_data)
