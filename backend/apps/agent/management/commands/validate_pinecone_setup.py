from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.agent.services.pinecone_api import describe_pinecone_index


class Command(BaseCommand):
    help = "Validate the configured Pinecone index for integrated-embedding RAG."

    def handle(self, *args, **options):
        if not settings.PINECONE_API_KEY:
            raise CommandError("PINECONE_API_KEY is missing in backend/.env.")
        if not settings.PINECONE_INDEX_NAME:
            raise CommandError("PINECONE_INDEX_NAME is missing in backend/.env.")

        try:
            description = describe_pinecone_index()
        except Exception as exc:
            raise CommandError(f"Failed to describe Pinecone index: {exc}") from exc

        embed = description.get("embed") or {}
        field_map = embed.get("field_map") or {}
        text_field = field_map.get("text")
        is_ready = description.get("status", {}).get("ready")

        self.stdout.write(f"Index name: {description.get('name')}")
        self.stdout.write(f"Host: {description.get('host')}")
        self.stdout.write(f"Ready: {is_ready}")
        self.stdout.write(f"Metric: {description.get('metric')}")
        self.stdout.write(f"Dimension: {description.get('dimension')}")
        self.stdout.write(f"Embed model: {embed.get('model', 'N/A')}")
        self.stdout.write(f"Field map text -> {text_field or 'N/A'}")

        warnings = []
        if not is_ready:
            warnings.append("Index is not ready yet.")
        if not embed:
            warnings.append("Index does not appear to have integrated embedding enabled.")
        if description.get("metric") != "cosine":
            warnings.append("Metric should be cosine for the current setup.")
        if settings.PINECONE_EMBEDDING_MODEL and embed.get("model") != settings.PINECONE_EMBEDDING_MODEL:
            warnings.append(
                f"Configured expected model is {settings.PINECONE_EMBEDDING_MODEL}, "
                f"but index reports {embed.get('model') or 'N/A'}."
            )
        if settings.PINECONE_TEXT_FIELD and text_field != settings.PINECONE_TEXT_FIELD:
            warnings.append(
                f"PINECONE_TEXT_FIELD is {settings.PINECONE_TEXT_FIELD}, "
                f"but index field_map uses {text_field or 'N/A'}."
            )

        if warnings:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Warnings:"))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"- {warning}"))
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("Pinecone setup looks valid for integrated-embedding RAG."))
