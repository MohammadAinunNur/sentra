"""Klasifikasi komentar yang belum diproses lalu jalankan workflow.

Pakai:  python manage.py process_mentions
"""
from collections import Counter

from django.core.management.base import BaseCommand

from apps.core.models import Topic
from apps.inbox.models import Mention
from apps.integrations.services.ai import classify
from apps.monitoring.models import log
from apps.workflow.services import run_workflow


class Command(BaseCommand):
    help = "Analisis AI untuk mention baru, lalu jalankan workflow (tiket, PIC, SLA)."

    def handle(self, *args, **options):
        topics = {t.name.lower(): t for t in Topic.objects.all()}
        engines = Counter()
        for mention in Mention.objects.filter(is_processed=False):
            result = classify(mention.content, [t.name for t in topics.values()])
            mention.sentiment = result["sentiment"]
            mention.sentiment_score = result["score"]
            mention.topic = topics.get(str(result["topic"]).lower())
            mention.priority = result["priority"]
            mention.ai_recommendation = result["recommendation"]
            mention.is_processed = True  # 1 komentar = 1 kali klasifikasi
            mention.save()
            run_workflow(mention)
            engines[result.get("engine", "rule")] += 1

        count = sum(engines.values())
        detail = ", ".join(f"{name}: {n}" for name, n in engines.items()) or "tidak ada data baru"
        log("Sentiment Engine", f"{count} mention diproses ({detail})")
        self.stdout.write(self.style.SUCCESS(f"{count} mention diproses ({detail})"))
