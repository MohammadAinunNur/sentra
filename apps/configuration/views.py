from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from apps.accounts.decorators import access_required
from apps.accounts.models import User
from apps.core.models import Keyword, Topic, Unit
from apps.integrations.models import SocialConnection
from apps.workflow.models import EscalationRule, SLAConfig, WorkflowRule

TABS = [
    ("connections", "Social Media Connection"),
    ("users", "User & Role"),
    ("workflow", "Workflow"),
    ("sla", "SLA & Escalation"),
    ("notification", "Notification"),
    ("ai", "AI Configuration"),
    ("master", "Master Data"),
]


@access_required("is_admin_role")
def index(request, tab="connections"):
    if tab not in dict(TABS):
        raise Http404
    context = {"tabs": TABS, "tab": tab}

    # Versi awal: tampilan baca-saja. Tambah/ubah data lewat Django Admin
    # (tombol "Kelola" di tiap tab).
    if tab == "connections":
        context["connections"] = SocialConnection.objects.all()
    elif tab == "users":
        context["users"] = User.objects.select_related("unit").order_by("role", "username")
    elif tab == "workflow":
        context["rules"] = WorkflowRule.objects.select_related("topic", "assign_unit")
    elif tab == "sla":
        context["slas"] = SLAConfig.objects.all()
        context["escalations"] = EscalationRule.objects.all()
    elif tab == "ai":
        context["ai"] = {
            "use_bedrock": settings.USE_BEDROCK,
            "model": settings.BEDROCK_MODEL_ID,
            "region": settings.AWS_REGION,
        }
    elif tab == "master":
        context.update(units=Unit.objects.all(), topics=Topic.objects.all(), keywords=Keyword.objects.all())
    return render(request, "configuration/index.html", context)