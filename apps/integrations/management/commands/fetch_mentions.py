"""Ambil komentar baru dari semua koneksi aktif.

Pakai:  python manage.py fetch_mentions
Jadwalkan dengan cron / EventBridge sesuai sync interval.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.integrations.models import SocialConnection
from apps.integrations.services.collectors import COLLECTORS, save_mentions
from apps.monitoring.models import log


class Command(BaseCommand):
    help = "Ambil komentar dari Instagram/YouTube dan simpan ke Inbox."

    def handle(self, *args, **options):
        for conn in SocialConnection.objects.filter(is_active=True):
            collector = COLLECTORS.get(conn.channel)
            if not collector:
                continue
            try:
                created = save_mentions(collector(conn))
                conn.status = SocialConnection.Status.CONNECTED
                log(f"{conn.get_channel_display()} API", f"{created} komentar baru diterima")
                self.stdout.write(f"{conn}: {created} komentar baru")
            except Exception as exc:  # jaringan, token kedaluwarsa, kuota habis
                conn.status = SocialConnection.Status.ERROR
                log(f"{conn.get_channel_display()} API", f"Gagal: {exc}", "failed")
                self.stderr.write(f"{conn}: {exc}")
            conn.last_sync = timezone.now()
            conn.save()