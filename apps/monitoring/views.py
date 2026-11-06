from django.shortcuts import render

from apps.accounts.decorators import access_required
from apps.inbox.models import Mention
from apps.integrations.models import SocialConnection
from apps.tickets.models import Ticket

from .models import ActivityLog


@access_required("can_manage_inbox")
def index(request):
    context = {
        "connections": SocialConnection.objects.all(),
        "incoming": Mention.objects.count(),
        "processed": Mention.objects.filter(is_processed=True).count(),
        "queue": Mention.objects.filter(is_processed=False).count(),
        "ticket_status": {
            label: Ticket.objects.filter(status=value).count()
            for value, label in Ticket.Status.choices
        },
        "escalated": Ticket.objects.filter(escalated=True).count(),
        "logs": ActivityLog.objects.all()[:20],
    }
    return render(request, "monitoring/index.html", context)