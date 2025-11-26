"""Example demonstrating the use of Agent Templates."""

import os
import asyncio
from craft.agents.templates import (
    CustomerSupportAgent,
    CodeReviewAgent,
    DataAnalystAgent,
    ResearchAgent,
    ContentWriterAgent
)

# Mock provider for testing without API keys if needed, 
# but here we assume the user might want to run it with real keys.
# For this verification, we just check instantiation and prompt generation.

async def main():
    print("🚀 Verifying Agent Templates...\n")
    
    # 1. Customer Support Agent
    support = CustomerSupportAgent(
        name="HelpDesk",
        tone="empathetic",
        company_name="TechCorp"
    )
    print(f"✅ Customer Support Agent: {support.name}")
    print(f"   Role: {support.role}")
    print(f"   Goal: {support.goal}")
    print(f"   Backstory: {support.backstory[:50]}...")
    print()

    # 2. Code Review Agent
    reviewer = CodeReviewAgent(
        name="PyReviewer",
        language="Python",
        focus="security"
    )
    print(f"✅ Code Review Agent: {reviewer.name}")
    print(f"   Role: {reviewer.role}")
    print(f"   Goal: {reviewer.goal}")
    print()

    # 3. Data Analyst Agent
    analyst = DataAnalystAgent(
        name="DataWiz",
        expertise="marketing analytics"
    )
    print(f"✅ Data Analyst Agent: {analyst.name}")
    print(f"   Role: {analyst.role}")
    print(f"   Goal: {analyst.goal}")
    print()

    # 4. Research Agent
    researcher = ResearchAgent(
        name="DeepSearch",
        depth="academic"
    )
    print(f"✅ Research Agent: {researcher.name}")
    print(f"   Role: {researcher.role}")
    print(f"   Goal: {researcher.goal}")
    print()

    # 5. Content Writer Agent
    writer = ContentWriterAgent(
        name="StoryTeller",
        style="witty",
        audience="developers"
    )
    print(f"✅ Content Writer Agent: {writer.name}")
    print(f"   Role: {writer.role}")
    print(f"   Goal: {writer.goal}")
    print()
    
    print("🎉 All templates instantiated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
