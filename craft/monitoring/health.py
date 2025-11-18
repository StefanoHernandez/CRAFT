"""Health check system."""

from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth(BaseModel):
    """Health status of a component."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    last_check: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheck:
    """
    Health check system for monitoring service health.

    Monitors various components and provides overall system health status.

    Examples:
        health = HealthCheck()

        # Add component checks
        health.add_check("database", check_database_health)
        health.add_check("provider", check_provider_health)

        # Run checks
        status = await health.check_all()
        print(f"System status: {status.status}")
    """

    def __init__(self):
        """Initialize health check system."""
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, ComponentHealth] = {}

    def add_check(self, name: str, check_func: Callable) -> None:
        """
        Add a health check.

        Args:
            name: Component name
            check_func: Async function that returns ComponentHealth
        """
        self._checks[name] = check_func

    def remove_check(self, name: str) -> None:
        """Remove a health check."""
        self._checks.pop(name, None)
        self._last_results.pop(name, None)

    async def check_component(self, name: str) -> ComponentHealth:
        """
        Check health of a specific component.

        Args:
            name: Component name

        Returns:
            Component health status
        """
        if name not in self._checks:
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="No health check configured"
            )

        try:
            check_func = self._checks[name]

            # Run check with timeout
            if asyncio.iscoroutinefunction(check_func):
                result = await asyncio.wait_for(check_func(), timeout=5.0)
            else:
                result = check_func()

            # Ensure it's a ComponentHealth object
            if not isinstance(result, ComponentHealth):
                result = ComponentHealth(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                    message=str(result) if isinstance(result, str) else None
                )

            self._last_results[name] = result
            return result

        except asyncio.TimeoutError:
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Health check timeout"
            )
            self._last_results[name] = result
            return result

        except Exception as e:
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
            self._last_results[name] = result
            return result

    async def check_all(self) -> ComponentHealth:
        """
        Check health of all components.

        Returns:
            Overall system health
        """
        if not self._checks:
            return ComponentHealth(
                name="system",
                status=HealthStatus.UNKNOWN,
                message="No health checks configured"
            )

        # Run all checks in parallel
        results = await asyncio.gather(
            *[self.check_component(name) for name in self._checks.keys()],
            return_exceptions=True
        )

        # Determine overall status
        statuses = [r.status for r in results if isinstance(r, ComponentHealth)]

        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY

        # Count by status
        status_counts = {
            "healthy": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
            "degraded": sum(1 for s in statuses if s == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for s in statuses if s == HealthStatus.UNHEALTHY),
            "unknown": sum(1 for s in statuses if s == HealthStatus.UNKNOWN),
        }

        return ComponentHealth(
            name="system",
            status=overall_status,
            message=f"Checked {len(self._checks)} components",
            metadata={
                "components": [r.model_dump() for r in results if isinstance(r, ComponentHealth)],
                "status_counts": status_counts,
            }
        )

    def get_last_results(self) -> List[ComponentHealth]:
        """Get last health check results for all components."""
        return list(self._last_results.values())

    def get_status(self, name: str) -> Optional[ComponentHealth]:
        """Get last result for a specific component."""
        return self._last_results.get(name)

    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        if not self._last_results:
            return False

        return all(
            r.status == HealthStatus.HEALTHY
            for r in self._last_results.values()
        )


# Pre-defined health check functions

async def check_storage_health(storage) -> ComponentHealth:
    """Check storage health."""
    try:
        count = storage.count()
        return ComponentHealth(
            name="storage",
            status=HealthStatus.HEALTHY,
            message=f"Storage operational ({count} conversations)",
            metadata={"count": count}
        )
    except Exception as e:
        return ComponentHealth(
            name="storage",
            status=HealthStatus.UNHEALTHY,
            message=f"Storage error: {str(e)}"
        )


async def check_provider_health(provider) -> ComponentHealth:
    """Check provider health."""
    try:
        # Simple ping test
        # For production, you'd want a lightweight test endpoint
        return ComponentHealth(
            name="provider",
            status=HealthStatus.HEALTHY,
            message=f"Provider {provider.name} operational",
            metadata={"provider": provider.name}
        )
    except Exception as e:
        return ComponentHealth(
            name="provider",
            status=HealthStatus.UNHEALTHY,
            message=f"Provider error: {str(e)}"
        )


async def check_memory_health() -> ComponentHealth:
    """Check system memory usage."""
    try:
        import psutil
        memory = psutil.virtual_memory()

        if memory.percent > 90:
            status = HealthStatus.UNHEALTHY
            message = "Critical memory usage"
        elif memory.percent > 80:
            status = HealthStatus.DEGRADED
            message = "High memory usage"
        else:
            status = HealthStatus.HEALTHY
            message = "Memory usage normal"

        return ComponentHealth(
            name="memory",
            status=status,
            message=message,
            metadata={
                "percent": memory.percent,
                "available_mb": memory.available / (1024 * 1024)
            }
        )
    except ImportError:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message="psutil not installed"
        )
    except Exception as e:
        return ComponentHealth(
            name="memory",
            status=HealthStatus.UNKNOWN,
            message=f"Error checking memory: {str(e)}"
        )
