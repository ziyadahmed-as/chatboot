from .vector_store import get_vector_store

_THRESHOLD = 0.7


async def retrieve(
    query: str,
    domain: str | None = None,
    top_k: int = 5,
) -> list[str]:
    """Retrieve relevant documents from the vector store.

    Returns up to top_k documents with cosine similarity >= 0.7.
    Returns an empty list if no documents meet the threshold.
    """
    store = get_vector_store()
    results = store.query(query_text=query, top_k=top_k, threshold=_THRESHOLD)
    return results
