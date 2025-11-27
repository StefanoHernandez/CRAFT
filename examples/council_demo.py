"""Council demo with LATEST AI models (Nov 2024)."""

import asyncio
from craft.agents.agent import Agent
from craft.providers.base import Provider, ProviderConfig, ChatResponse
from craft.consensus.council import Council, CouncilConfig, ConsensusStrategy

# Mock provider for demo (replace with real providers)
class MockProvider(Provider):
    """Mock provider for testing."""
    def __init__(self, model_name="mock"):
        super().__init__(ProviderConfig(model=model_name))
        self._display_name = model_name
        
    def _validate_config(self):
        pass
    
    def chat(self, messages, **kwargs):
        """Sync chat (not used in async demo)."""
        pass
        
    async def achat(self, messages, **kwargs):
        await asyncio.sleep(0.1)
        last_m = messages[-1]
        content = last_m.content if hasattr(last_m, 'content') else last_m['content']
        
        # Context-aware responses based on model
        if "gemini" in self._display_name.lower():
            response = f"[Gemini 2.0] Analysis: {content[:30]}..."
        elif "claude" in self._display_name.lower():
            response = f"[Claude 3.5] Critical view: {content[:30]}..."
        elif "grok" in self._display_name.lower():
            response = f"[Grok 4.1] Real-time insight: {content[:30]}..."
        elif "mistral" in self._display_name.lower():
            response = f"[Mistral Large] European perspective: {content[:30]}..."
        elif "gpt" in self._display_name.lower():
            response = f"[GPT-4o] Creative take: {content[:30]}..."
        else:
            response = f"[{self._display_name}] Response to: {content[:30]}..."
            
        return ChatResponse(content=response, role="assistant", model=self._display_name)

async def main():
    print("🏛️  CRAFT Council - Latest AI Models Demo\n")
    print("=" * 60)
    
    # Chairman: Gemini 2.0 Flash (Google's latest - Dec 2024)
    chairman = Agent(
        name="Chairman",
        provider=MockProvider("google/gemini-2.0-flash-exp"),
        role="Council Chairman",
        goal="Synthesize diverse viewpoints"
    )
    
    # Strategist: Claude 3.5 Sonnet (Anthropic's best - Oct 2024)
    strategist = Agent(
        name="Strategist",
        provider=MockProvider("anthropic/claude-sonnet-4.5"),
        role="Strategic Analyst",
        goal="Provide deep analysis"
    )
    
    # Innovator: GPT-4o (OpenAI multimodal)
    innovator = Agent(
        name="Innovator",
        provider=MockProvider("openai/gpt-4o"),
        role="Innovation Lead",
        goal="Think creatively"
    )
    
    # Expert: Mistral Large (French AI - GDPR compliant)
    expert = Agent(
        name="Expert",
        provider=MockProvider("mistralai/mistral-large-latest"),
        role="Technical Expert",
        goal="European compliance perspective"
    )
    
    # Trendsetter: Grok 4.1 (xAI with X data)
    trendsetter = Agent(
        name="Trendsetter",
        provider=MockProvider("x-ai/grok-4.1"),
        role="Trend Analyst",
        goal="Real-time market insights"
    )
    
    print("\n📋 Council Composition:")
    print(f"  👔 {chairman.name}: {chairman.provider._display_name}")
    print(f"  🎯 {strategist.name}: {strategist.provider._display_name}")
    print(f"  💡 {innovator.name}: {innovator.provider._display_name}")
    print(f"  🇪🇺 {expert.name}: {expert.provider._display_name}")
    print(f"  📈 {trendsetter.name}: {trendsetter.provider._display_name}")
    
    # Create Council
    council = Council(config=CouncilConfig(
        name="AI Elite Council 2024",
        strategy=ConsensusStrategy.DEBATE,
        agents=[strategist, innovator, expert, trendsetter],
        chairman=chairman,
        max_rounds=2
    ))
    
    # Deliberate
    topic = "Should we invest in quantum computing for our AI infrastructure?"
    print(f"\n📢 Topic: {topic}\n")
    
    result = await council.deliberate(topic)
    
    # Display results
    print("\n" + "="*60)
    print("⚖️  FINAL DECISION")
    print("="*60)
    print(f"\n{result.decision}")
    print(f"\n📊 Stats:")
    print(f"  • Iterations: {result.iterations}")
    print(f"  • Consensus: {result.consensus_reached}")
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  CRAFT Council - Multi-Provider AI Consensus System        ║
║  Featuring the LATEST models (November 2024)               ║
╚════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
