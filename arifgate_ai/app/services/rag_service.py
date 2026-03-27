"""
RAG service using LangChain + ChromaDB + OpenAI.

- Vector store: Chroma (in-memory by default, persistent if CHROMA_PERSIST_DIR is set)
- Embeddings:   OpenAI text-embedding-3-small
- LLM:          ChatOpenAI (model from OPENAI_MODEL env var, default gpt-4o)
- Retrieval:    Top-3 most relevant chunks injected as context before the user message
"""
import os
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

_EMBED_MODEL = "text-embedding-3-small"
_COLLECTION = "arifgate_knowledge"
_TOP_K = 3


@lru_cache(maxsize=1)
def _embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=_EMBED_MODEL,
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )


@lru_cache(maxsize=1)
def _vector_store() -> Chroma:
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    return Chroma(
        collection_name=_COLLECTION,
        embedding_function=_embeddings(),
        persist_directory=persist_dir,  # None = in-memory
    )


@lru_cache(maxsize=1)
def _llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        openai_api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.7,
        request_timeout=30,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest(texts: list[str], domain: str | None = None) -> int:
    """Embed and store documents. Returns number of documents ingested."""
    if not texts:
        return 0
    metadatas = [{"domain": domain or "general"} for _ in texts]
    _vector_store().add_texts(texts=texts, metadatas=metadatas)
    return len(texts)


def _retrieve(query: str) -> list[str]:
    """Return top-k relevant document chunks for a query."""
    store = _vector_store()
    # Only retrieve if the store has documents
    try:
        docs = store.similarity_search(query, k=_TOP_K)
        return [doc.page_content for doc in docs]
    except Exception:
        return []


async def chat(
    system_prompt: str,
    history: list[dict],
    user_message: str,
) -> str:
    """
    Run a RAG-augmented chat turn.

    1. Retrieve relevant context from the vector store.
    2. Build the message list: system → history → (context if any) → user.
    3. Call ChatOpenAI and return the reply string.
    """
    retrieved = _retrieve(user_message)

    messages = [SystemMessage(content=system_prompt)]

    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        elif turn["role"] == "assistant":
            messages.append(AIMessage(content=turn["content"]))

    if retrieved:
        context_block = "\n\n".join(retrieved)
        messages.append(
            SystemMessage(content=f"Relevant platform knowledge:\n{context_block}")
        )

    messages.append(HumanMessage(content=user_message))

    response = await _llm().ainvoke(messages)
    return response.content
