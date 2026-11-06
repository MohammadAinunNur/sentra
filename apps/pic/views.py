from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from apps.core.utils import pct
from apps.tickets.models import Ticket
from apps.tickets.services import visible_tickets

# Tiket dianggap "mendekati batas SLA" bila jatuh tempo dalam N jam ke depan
NEAR_SLA_HOURS = 4


@login_required
@never_cache  # supaya setelah keluar akun, tombol Back tidak menampilkan dasbor lagi
def dashboard(request):
    user = request.user

    # Halaman ini khusus PIC (superuser boleh lihat). Role lain kembali ke dashboard biasa.
    if user.role != user.Role.PIC and not user.is_superuser:
        return redirect("pic:dashboard")

    now = timezone.now()
    near_limit = now + timedelta(hours=NEAR_SLA_HOURS)
    S = Ticket.Status
    open_q = Q(status__in=Ticket.OPEN_STATUSES)

    # Hanya tiket milik PIC / unitnya (memakai aturan yang sudah ada di tickets.services)
    qs = visible_tickets(user)

    s = qs.aggregate(
        total=Count("id"),
        open=Count("id", filter=Q(status=S.OPEN)),
        in_progress=Count("id", filter=Q(status=S.IN_PROGRESS)),
        waiting=Count("id", filter=Q(status=S.WAITING)),
        resolved=Count("id", filter=Q(status=S.RESOLVED)),
        late_open=Count("id", filter=open_q & Q(due_at__lt=now)),
        late_done=Count("id", filter=Q(status=S.RESOLVED, resolved_at__gt=F("due_at"))),
        near=Count("id", filter=open_q & Q(due_at__gte=now, due_at__lte=near_limit)),
        p_critical=Count("id", filter=open_q & Q(priority="critical")),
        p_high=Count("id", filter=open_q & Q(priority="high")),
        p_medium=Count("id", filter=open_q & Q(priority="medium")),
        p_low=Count("id", filter=open_q & Q(priority="low")),
    )

    total = s["total"]
    late = s["late_open"] + s["late_done"]
    near = s["near"]
    on_time = max(total - late - near, 0)
    on_pct = pct(on_time, total)
    near_pct = pct(near, total)

    open_total = s["open"] + s["in_progress"] + s["waiting"]
    priorities = [
        ("Critical", "critical", s["p_critical"]),
        ("High", "high", s["p_high"]),
        ("Medium", "medium", s["p_medium"]),
        ("Low", "low", s["p_low"]),
    ]
    priority_rows = [
        {"label": label, "key": key, "count": n, "pct": pct(n, open_total)}
        for label, key, n in priorities
    ]

    urgent = (
        qs.filter(open_q)
        .select_related("topic", "unit")
        .order_by(F("due_at").asc(nulls_last=True))[:5]
    )
    latest = qs.select_related("topic").order_by("-updated_at")[:6]

    context = {
        "s": s,
        "open_total": open_total,
        "has_data": total > 0,
        "sla_pct": on_pct if total else 100,
        "on_time": on_time,
        "near": near,
        "late": late,
        "on_pct": on_pct,
        "near_end": on_pct + near_pct,  # batas akhir segmen kuning di donut
        "priority_rows": priority_rows,
        "urgent": urgent,
        "latest": latest,
        "near_hours": NEAR_SLA_HOURS,
    }
    return render(request, "pic/dashboard.html", context)