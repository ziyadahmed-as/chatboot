import os
from abc import ABC, abstractmethod

import numpy as np
import openai

_EMBED_MODEL = "text-embedding-3-small"


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    response = client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class VectorStoreAdapter(ABC):
    @abstractmethod
    def add(self, texts: list[str], domain: str | None) -> None:
        """Embed and store documents, optionally tagged with a domain."""

    @abstractmethod
    def query(self, query_text: str, top_k: int, threshold: float) -> list[str]:
        """Return up to top_k documents with similarity >= threshold."""


class ChromaDBAdapter(VectorStoreAdapter):
    def __init__(self, persist_dir: str | None = None):
        import chromadb

        if persist_dir:
            self._client = chromadb.PersistentClient(path=persist_dir)
        else:
            self._client = chromadb.Client()

        self._collection = self._client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, texts: list[str], domain: str | None) -> None:
        if not texts:
            return
        embeddings = _get_embeddings(texts)
        # Use a simple incrementing ID based on current count
        start_id = self._collection.count()
        ids = [str(start_id + i) for i in range(len(texts))]
        metadatas = [{"domain": domain or ""} for _ in texts]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def query(self, query_text: str, top_k: int, threshold: float) -> list[str]:
        if self._collection.count() == 0:
            return []
        embedding = _get_embeddings([query_text])[0]
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "distances"],
        )
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        # ChromaDB cosine space returns distances where 0 = identical, 2 = opposite
        # similarity = 1 - (distance / 2) for normalized vectors, or simply 1 - distance
        # when using hnsw:space=cosine, distance = 1 - cosine_similarity
        filtered = [
            doc
            for doc, dist in zip(docs, distances)
            if (1.0 - dist) >= threshold
        ]
        return filtered


class FAISSAdapter(VectorStoreAdapter):
    def __init__(self):
        self._texts: list[str] = []
        self._domains: list[str | None] = []
        self._embeddings: list[list[float]] = []
        self._dim: int | None = None

    def add(self, texts: list[str], domain: str | None) -> None:
        if not texts:
            return
        embeddings = _get_embeddings(texts)
        self._texts.extend(texts)
        self._domains.extend([domain] * len(texts))
        self._embeddings.extend(embeddings)
        if self._dim is None and embeddings:
            self._dim = len(embeddings[0])

    def query(self, query_text: str, top_k: int, threshold: float) -> list[str]:
        if not self._embeddings:
            return []
        query_emb = _get_embeddings([query_text])[0]
        scored = [
            (self._texts[i], _cosine_similarity(query_emb, self._embeddings[i]))
            for i in range(len(self._embeddings))
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [text for text, score in scored[:top_k] if score >= threshold]


def get_vector_store() -> VectorStoreAdapter:
    backend = os.environ.get("RAG_BACKEND", "chromadb").lower()
    if backend == "faiss":
        return FAISSAdapter()
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR")
    return ChromaDBAdapter(persist_dir=persist_dir)
