from apps.monitoring.models import log
from apps.tickets.services import create_ticket_from_mention

from .models import WorkflowRule
from .notifications import notify


def run_workflow(mention):
    """Cari rule pertama yang cocok lalu jalankan aksinya. Mengembalikan tiket (atau None)."""
    if mention.tickets.exists():
        return None

    for rule in WorkflowRule.objects.filter(is_active=True):
        if not rule.matches(mention):
            continue
        ticket = None
        if rule.create_ticket:
            ticket = create_ticket_from_mention(mention, unit=rule.assign_unit)
            log("Workflow", f"Rule '{rule.name}' membuat tiket {ticket.code}")
        if rule.send_notification and ticket:
            notify(ticket.pic, f"Tiket baru {ticket.code} ({ticket.priority})", ("email", "in_app"))
        return ticket
    return None