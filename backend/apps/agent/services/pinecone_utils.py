import os
import re

from django.conf import settings


ROLL_NO_PATTERN = re.compile(r"Student Roll No:\s*([A-Za-z0-9_-]+)", re.IGNORECASE)


def normalize_namespace_value(value: str) -> str:
    """Keep namespace values predictable and Pinecone-safe."""
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", (value or "").strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "anonymous"


def get_public_namespace() -> str:
    """Shared namespace for university-wide knowledge."""
    if settings.configured:
        raw_namespace = getattr(
            settings,
            "PINECONE_PUBLIC_NAMESPACE",
            getattr(settings, "PINECONE_NAMESPACE", "kfueit_public"),
        )
    else:
        raw_namespace = os.getenv("PINECONE_PUBLIC_NAMESPACE") or os.getenv(
            "PINECONE_NAMESPACE",
            "kfueit_public",
        )
    return normalize_namespace_value(raw_namespace)


def build_student_namespace(roll_no: str) -> str:
    """Stable per-student namespace derived from roll number."""
    return f"student_{normalize_namespace_value(roll_no)}"


def resolve_namespace(
    roll_no: str | None = None,
    namespace: str | None = None,
    use_public_default: bool = True,
) -> str:
    if namespace:
        return normalize_namespace_value(namespace)
    if roll_no:
        return build_student_namespace(roll_no)
    return get_public_namespace() if use_public_default else ""


def get_query_namespaces(
    roll_no: str | None = None,
    include_public_fallback: bool = True,
) -> list[str]:
    namespaces: list[str] = []
    if roll_no:
        namespaces.append(build_student_namespace(roll_no))
    if include_public_fallback:
        public_namespace = get_public_namespace()
        if public_namespace not in namespaces:
            namespaces.append(public_namespace)
    return namespaces


def extract_roll_no_from_text(text: str) -> str:
    match = ROLL_NO_PATTERN.search(text or "")
    return (match.group(1) if match else "").strip()
