from apps.core.models import Komentar
from apps.tickets.models import Ticket


def notifications_context(request):
    """
    Menyediakan data notifikasi real-time untuk ikon lonceng di topbar
    serta nilai filter default yang aman untuk form filter topbar di base.html.
    """
    # Ambil filter params secara aman via request.GET.get() agar tidak memicu MultiValueDictKeyError di template
    q_param = request.GET.get("q", "").strip() if hasattr(request, "GET") else ""
    period_param = request.GET.get("period", "").strip() if hasattr(request, "GET") else ""
    start_date_param = request.GET.get("start_date", "").strip() if hasattr(request, "GET") else ""
    end_date_param = request.GET.get("end_date", "").strip() if hasattr(request, "GET") else ""

    base_context = {
        "nav_q": q_param,
        "nav_period": period_param or "all",
        "nav_start_date": start_date_param,
        "nav_end_date": end_date_param,
        "notif_open_tickets": [],
        "notif_open_tickets_count": 0,
        "notif_critical_comments": [],
        "notif_critical_comments_count": 0,
        "notif_count": 0,
    }

    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return base_context

    try:
        # 1. Tiket terbuka / butuh penanganan
        open_tickets = list(
            Ticket.objects.filter(status__in=Ticket.OPEN_STATUSES)
            .select_related("topic")
            .order_by("-created_at")[:5]
        )
        open_tickets_count = Ticket.objects.filter(status__in=Ticket.OPEN_STATUSES).count()

        # 2. Komentar ber-sentimen negatif yang perlu perhatian
        critical_comments = list(
            Komentar.objects.filter(sentiment="NEGATIVE").order_by("-dibuat_pada")[:5]
        )
        critical_comments_count = Komentar.objects.filter(sentiment="NEGATIVE").count()

        total_notif_count = open_tickets_count + critical_comments_count

        base_context.update({
            "notif_open_tickets": open_tickets,
            "notif_open_tickets_count": open_tickets_count,
            "notif_critical_comments": critical_comments,
            "notif_critical_comments_count": critical_comments_count,
            "notif_count": total_notif_count,
        })
        return base_context
    except Exception:
        return base_context
