from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.models import Komentar
from apps.tickets.models import Ticket

from .utils import pct


@login_required
def dashboard(request):
    user = request.user
    # PIC langsung diarahkan ke daftar tiket miliknya
    if user.role == user.Role.PIC and not user.is_superuser:
        return redirect("pic:dashboard")

    # 1. Mengambil data asli dari model Komentar (Instagram)
    komentar_qs = Komentar.objects.all()
    total_komentar = komentar_qs.count()

    # 2. Hitung jumlah dan persentase berdasarkan sentimen dari database
    positive_count = komentar_qs.filter(sentiment='POSITIVE').count()
    neutral_count = komentar_qs.filter(sentiment='NEUTRAL').count()
    negative_count = komentar_qs.filter(sentiment='NEGATIVE').count()

    positive_pct = pct(positive_count, total_komentar)
    neutral_pct = pct(neutral_count, total_komentar)
    negative_pct = pct(negative_count, total_komentar)

    # 3. Ambil data statistik Tiket dari database
    tickets = Ticket.objects.all()
    total_tickets = tickets.count()
    open_tickets = tickets.filter(status__in=Ticket.OPEN_STATUSES).count()
    escalated = tickets.filter(escalated=True).count()

    # 4. Ambil 15 komentar Instagram terbaru untuk tabel
    komentar_list = komentar_qs.order_by("-dibuat_pada")[:15]

    # 5. Ambil komentar negatif/kritis untuk widget Critical Mentions
    critical_comments = komentar_qs.filter(sentiment='NEGATIVE').order_by("-dibuat_pada")[:5]

    context = {
        # Total Mentions menggunakan total Komentar Instagram asli
        "total": total_komentar,
        
        # Statistik Tiket & SLA
        "open_tickets": open_tickets,
        "sla_compliance": 100 - pct(escalated, total_tickets) if total_tickets else 100,
        
        # Data Komentar Instagram Asli & Critical Mentions
        "komentar_list": komentar_list,
        "critical": critical_comments,
        
        # Nilai Sentimen Dinamis dari Database
        "positive": positive_count,
        "neutral": neutral_count,
        "negative": negative_count,
        "positive_pct": positive_pct,
        "neutral_pct": neutral_pct,
        "negative_pct": negative_pct,
    }
       

    return render(request, "core/dashboard.html", context)