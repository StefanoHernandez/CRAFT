
import os
from craft.agents import Agent
from craft.providers import AnthropicProvider
from craft.rag import RetrievalEngine, RetrievalConfig, ChunkingStrategy, ChunkConfig
from craft.rag.embeddings import SentenceTransformerEmbedding
from craft.rag.vectorstores import ChromaVectorStore

# 1. Setup RAG Components
# Embeddings
embeddings = SentenceTransformerEmbedding(model_name="all-MiniLM-L6-v2")

# Vector Store
vector_store = ChromaVectorStore(
    collection_name="craft_docs",
    persist_directory="./chroma_db"
)

# Retrieval Engine configuration
config = RetrievalConfig(
    chunk_config=ChunkConfig(
        strategy=ChunkingStrategy.SEMANTIC,
        chunk_size=500
    ),
    top_k=3,
    hybrid_search=True  # Enable dense + sparse search
)

rag = RetrievalEngine(
    embedding_provider=embeddings,
    vector_store=vector_store,
    config=config
)

# 2. Add Documents
documents = [
    "CRAFT v2.0 introduces autonomous agents with roles and goals.",
    "The Council system allows multiple agents to debate and reach consensus.",
    "Tools in CRAFT are type-safe and use Pydantic for validation.",
    "CRAFT supports hybrid search using Reciprocal Rank Fusion (RRF)."
]
rag.add_documents(documents, chunk=True)

# 3. Create Agent with RAG
agent = Agent(
    name="SupportBot",
    role="Documentation Assistant",
    goal="Answer questions about CRAFT framework",
    provider=AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY")),
    rag=rag,  # Inject RAG engine
    verbose=True
)

# 4. Ask Questions
question = "How does multi-agent collaboration work in CRAFT?"
print(f"Question: {question}\n")

result = agent.run(question)

print("\n--- Answer ---")
print(result.text)
