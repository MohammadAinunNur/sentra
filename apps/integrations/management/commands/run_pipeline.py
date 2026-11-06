"""Jalankan seluruh alur otomatis: ambil komentar -> analisis AI -> cek SLA.

Pakai:  python manage.py run_pipeline              (sekali jalan)
        python manage.py run_pipeline --every 15   (ulangi tiap 15 menit)
"""
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.monitoring.models import log

STEPS = ("fetch_mentions", "process_mentions", "check_sla")


class Command(BaseCommand):
    help = "Jalankan fetch_mentions, process_mentions, dan check_sla berurutan."

    def add_arguments(self, parser):
        parser.add_argument("--every", type=int, default=0,
                            help="Ulangi tiap N menit (0 = sekali saja)")

    def handle(self, *args, **options):
        every = options["every"]
        while True:
            for step in STEPS:
                try:  # satu langkah gagal tidak boleh menghentikan langkah lain
                    call_command(step)
                except Exception as exc:
                    log("Pipeline", f"{step} gagal: {type(exc).__name__}: {exc}", "failed")
                    self.stderr.write(f"{step} gagal: {exc}")
            if not every:
                break
            self.stdout.write(f"Selesai. Menunggu {every} menit (Ctrl+C untuk berhenti)...")
            try:
                time.sleep(every * 60)
            except KeyboardInterrupt:
                self.stdout.write("Dihentikan.")
                break
