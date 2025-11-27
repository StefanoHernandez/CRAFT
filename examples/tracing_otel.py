"""
Example: OpenTelemetry Integration with CRAFT Tracing

This example demonstrates how to use OpenTelemetry exporters (Jaeger, OTLP)
with CRAFT's existing tracing system.

Requirements:
    pip install 'craft-chatbot[opentelemetry]'

Running Jaeger locally (Docker):
    docker run -d \\
        -p 16686:16686 \\
        -p 6831:6831/udp \\
        jaegertracing/all-in-one:latest
    
    Then open http://localhost:16686 to view traces
"""

import os
import asyncio
from craft.agents import Agent
from craft.providers import OpenAIProvider
from craft.tools import tool
from craft.tracing import tracer

# Configure OpenTelemetry
os.environ["CRAFT_TRACE_CLIENT_IO"] = "2"  # Enable CRAFT tracing (level 2)
os.environ["OTEL_EXPORTER_TYPE"] = "jaeger"  # jaeger | otlp | console
os.environ["OTEL_SERVICE_NAME"] = "craft-demo-agent"
os.environ["JAEGER_AGENT_HOST"] = "localhost"
os.environ["JAEGER_AGENT_PORT"] = "6831"


# Define custom tools
@tool
def search_database(query: str) -> str:
    """Search internal database."""
    # Simulate DB query
    return f"Found 5 results for: {query}"


@tool
def analyze_data(data: str) -> dict:
    """Analyze data and return insights."""
    return {
        "total_records": 100,
        "insights": f"Analysis of {data}",
        "confidence": 0.95
    }


async def main():
    print("🔍 CRAFT + OpenTelemetry Demo")
    print("=" * 50)
    
    # Create agent with tools
    agent = Agent(
        name="DataAgent",
        role="Data Analyst",
        goal="Analyze sales data and provide insights",
        provider=OpenAIProvider(model="gpt-4o"),
        tools=[search_database, analyze_data],
        verbose=True
    )
    
    # Run agent - traces will be sent to both:
    # 1. Console (CRAFT's beautiful format)
    # 2. Jaeger UI (http://localhost:16686)
    
    print("\n🚀 Running agent...")
    result = await agent.arun("Search for Q3 sales data and analyze it")
    
    print("\n✅ Result:", result.text)
    
    # Flush OTel spans before exit
    from craft.tracing.otel_bridge import shutdown_otel
    shutdown_otel()
    
    print("\n📊 View traces in Jaeger:")
    print("   http://localhost:16686")
    print("   Service: craft-demo-agent")


if __name__ == "__main__":
    # Note: Replace with your actual API key or set OPENAI_API_KEY env var
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    asyncio.run(main())
