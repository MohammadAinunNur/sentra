"""Periksa SLA tiket terbuka: kirim reminder di 80% dan eskalasi bila terlewat.

Pakai:  python manage.py check_sla
Jadwalkan tiap 5-10 menit (cron / EventBridge).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tickets.models import Ticket
from apps.workflow.notifications import notify


class Command(BaseCommand):
    help = "Reminder SLA dan eskalasi otomatis."

    def handle(self, *args, **options):
        now = timezone.now()
        reminded = escalated = 0
        for t in Ticket.objects.filter(status__in=Ticket.OPEN_STATUSES, due_at__isnull=False):
            total = (t.due_at - t.created_at).total_seconds()
            elapsed = (now - t.created_at).total_seconds()

            if now > t.due_at and not t.escalated:
                t.escalated = True
                t.save(update_fields=["escalated", "updated_at"])
                t.add_history("Eskalasi otomatis", "SLA terlewati")
                notify(t.pic, f"ESKALASI {t.code}: SLA terlewati", ("email", "whatsapp", "in_app"))
                escalated += 1
            elif total and elapsed / total >= 0.8 and not t.reminded:
                t.reminded = True
                t.save(update_fields=["reminded", "updated_at"])
                t.add_history("Reminder SLA", "80% waktu SLA terpakai")
                notify(t.pic, f"Reminder {t.code}: SLA hampir habis", ("email", "whatsapp"))
                reminded += 1
        self.stdout.write(self.style.SUCCESS(f"{reminded} reminder, {escalated} eskalasi"))