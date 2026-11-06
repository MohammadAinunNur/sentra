"""Uji mesin AI dengan satu kalimat. Error Bedrock ditampilkan apa adanya.

Pakai:  python manage.py test_ai
        python manage.py test_ai "Debu batubara parah, kapan ditangani?"
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.models import Topic
from apps.integrations.services.ai import classify


class Command(BaseCommand):
    help = "Uji klasifikasi AI untuk satu komentar."

    def add_arguments(self, parser):
        parser.add_argument("text", nargs="?", default="Unit 9 kok sering padam ya? Mohon penjelasan")

    def handle(self, *args, **options):
        mode = "Bedrock" if settings.USE_BEDROCK else "kata kunci (USE_BEDROCK=0)"
        self.stdout.write(f"Mode   : {mode}")
        self.stdout.write(f"Model  : {settings.BEDROCK_MODEL_ID}")
        self.stdout.write(f"Region : {settings.AWS_REGION}")
        try:
            result = classify(options["text"], [t.name for t in Topic.objects.all()], strict=True)
        except Exception as exc:
            raise CommandError(f"Bedrock gagal: {type(exc).__name__}: {exc}")
        self.stdout.write("Hasil  :")
        for key, value in result.items():
            self.stdout.write(f"  {key}: {value}")
