from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.agent.services.pinecone_utils import (
    build_student_namespace,
    get_public_namespace,
    resolve_namespace,
)
from apps.agent.services.scraper import scrape_and_index_all


class Command(BaseCommand):
    help = "Index KFUEIT knowledge into a student's Pinecone namespace or the shared public namespace."

    def add_arguments(self, parser):
        parser.add_argument(
            "roll_no",
            nargs="?",
            help="Student roll number for per-student namespace indexing.",
        )
        parser.add_argument(
            "--public",
            action="store_true",
            help="Index into the shared public namespace instead of a student namespace.",
        )
        parser.add_argument(
            "--namespace",
            help="Override the target namespace explicitly.",
        )

    def handle(self, *args, **options):
        roll_no = (options.get("roll_no") or "").strip()
        use_public = options.get("public", False)
        custom_namespace = (options.get("namespace") or "").strip()

        if not settings.OPENAI_API_KEY:
            self.stdout.write(self.style.WARNING("OPENAI_API_KEY is not required for Pinecone-integrated embeddings."))
        if not settings.PINECONE_API_KEY:
            raise CommandError("PINECONE_API_KEY is missing in backend/.env.")
        if not settings.PINECONE_INDEX_NAME:
            raise CommandError("PINECONE_INDEX_NAME is missing in backend/.env.")

        if use_public and roll_no:
            raise CommandError("Provide either a roll number or --public, not both.")
        if not any([roll_no, use_public, custom_namespace]):
            raise CommandError("Provide a roll number, or use --public, or pass --namespace.")

        if roll_no and not custom_namespace:
            self._validate_student_exists(roll_no)

        target_namespace = resolve_namespace(
            roll_no=roll_no if not use_public else None,
            namespace=custom_namespace or None,
            use_public_default=use_public,
        )

        self.stdout.write(self.style.NOTICE(f"Target Pinecone index: {settings.PINECONE_INDEX_NAME}"))
        self.stdout.write(self.style.NOTICE(f"Target namespace: {target_namespace}"))
        if roll_no and not custom_namespace:
            self.stdout.write(self.style.NOTICE(f"Derived from student: {roll_no}"))
            self.stdout.write(self.style.NOTICE(f"Expected student namespace: {build_student_namespace(roll_no)}"))
        if use_public and not custom_namespace:
            self.stdout.write(self.style.NOTICE(f"Shared public namespace: {get_public_namespace()}"))

        try:
            scrape_and_index_all(
                roll_no=roll_no if not use_public else None,
                namespace=target_namespace,
            )
        except Exception as exc:
            raise CommandError(f"Indexing failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Pinecone indexing completed successfully."))

    def _validate_student_exists(self, roll_no: str):
        from apps.agent.models import StudentProfile

        if not StudentProfile.objects.filter(roll_no=roll_no).exists():
            raise CommandError(f"Student with roll number {roll_no} does not exist.")
