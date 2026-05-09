from django.conf import settings


def _get_index():
    from pinecone import Pinecone
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    configured_host = (settings.PINECONE_HOST or "").strip()
    if configured_host:
        return pc.Index(host=configured_host)
    return pc.Index(settings.PINECONE_INDEX_NAME)


def describe_pinecone_index() -> dict:
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    info = pc.describe_index(settings.PINECONE_INDEX_NAME)
    if hasattr(info, "to_dict") and callable(info.to_dict):
        return info.to_dict()
    if isinstance(info, dict):
        return info
    if hasattr(info, "__dict__"):
        return dict(info.__dict__)
    raise TypeError(f"Unsupported Pinecone describe_index response type: {type(info)!r}")


def get_pinecone_index_host() -> str:
    info = describe_pinecone_index()
    return info.get("host", "")


def upsert_text_records(namespace: str, records: list[dict]) -> dict:
    if not records:
        return {"upserted_count": 0}
    index = _get_index()
    index.upsert_records(namespace, records)
    return {"upserted_count": len(records)}


def search_text_records(namespace: str, query_text: str, top_k: int, fields: list[str]) -> dict:
    index = _get_index()
    results = index.search_records(
        namespace=namespace,
        query={"inputs": {"text": query_text}, "top_k": top_k},
        fields=fields,
    )
    hits = results["result"]["hits"]
    return {"result": {"hits": hits}, "usage": results.get("usage", {})}
