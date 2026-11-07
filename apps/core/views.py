import json
from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.core.models import Komentar, Topic
from apps.tickets.models import Ticket

from .utils import pct


def make_dt_aware(dt):
    """Pastikan objek datetime memiliki info timezone yang sesuai settings Django."""
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


@login_required
def dashboard(request):
    user = request.user
    # PIC langsung diarahkan ke daftar tiket miliknya
    if user.role == user.Role.PIC and not user.is_superuser:
        return redirect("pic:dashboard")

    # Ambil parameter pencarian dan filter tanggal
    q = request.GET.get("q", "").strip()
    period = request.GET.get("period", "").strip()
    start_date_str = request.GET.get("start_date", "").strip()
    end_date_str = request.GET.get("end_date", "").strip()
    sentiment_filter = request.GET.get("sentiment", "").strip()

    now = timezone.now()
    today = now.date()

    # QuerySet dasar
    komentar_qs = Komentar.objects.all()

    # Logika filter tanggal menggunakan datetime langsung (menghindari issue MySQL CONVERT_TZ jika timezone tables belum di-load)
    filter_label = ""

    if period == "today":
        start_dt = make_dt_aware(datetime.combine(today, time.min))
        end_dt = make_dt_aware(datetime.combine(today, time.max))
        komentar_qs = komentar_qs.filter(dibuat_pada__gte=start_dt, dibuat_pada__lte=end_dt)
        filter_label = "Hari Ini"
    elif period == "7d":
        start_dt = make_dt_aware(datetime.combine(today - timedelta(days=7), time.min))
        komentar_qs = komentar_qs.filter(dibuat_pada__gte=start_dt)
        filter_label = "7 Hari Terakhir"
    elif period == "30d":
        start_dt = make_dt_aware(datetime.combine(today - timedelta(days=30), time.min))
        komentar_qs = komentar_qs.filter(dibuat_pada__gte=start_dt)
        filter_label = "30 Hari Terakhir"
    elif period == "this_month":
        start_of_month = today.replace(day=1)
        start_dt = make_dt_aware(datetime.combine(start_of_month, time.min))
        komentar_qs = komentar_qs.filter(dibuat_pada__gte=start_dt)
        filter_label = "Bulan Ini"
    elif period == "all":
        filter_label = "Semua Waktu"
    else:
        # Filter berdasarkan input manual tanggal mulai dan tanggal selesai
        s_date = None
        e_date = None
        if start_date_str:
            try:
                s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                start_dt = make_dt_aware(datetime.combine(s_date, time.min))
                komentar_qs = komentar_qs.filter(dibuat_pada__gte=start_dt)
            except ValueError:
                start_date_str = ""
        if end_date_str:
            try:
                e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                end_dt = make_dt_aware(datetime.combine(e_date, time.max))
                komentar_qs = komentar_qs.filter(dibuat_pada__lte=end_dt)
            except ValueError:
                end_date_str = ""

        if s_date and e_date:
            filter_label = (
                f"{s_date.strftime('%d %b %Y')} - {e_date.strftime('%d %b %Y')}"
            )
        elif s_date:
            filter_label = f"Mulai {s_date.strftime('%d %b %Y')}"
        elif e_date:
            filter_label = f"Sampai {e_date.strftime('%d %b %Y')}"
        else:
            filter_label = "Semua Waktu"

    # Filter kata kunci pencarian teks / username / caption komentar
    if q:
        komentar_qs = komentar_qs.filter(
            Q(comment_text__icontains=q)
            | Q(username__icontains=q)
            | Q(caption__icontains=q)
        )
        if filter_label and filter_label != "Semua Waktu":
            filter_label = f"{filter_label} ('{q}')"
        else:
            filter_label = f"Cari: '{q}'"

    # Filter sentimen jika dipilih
    if sentiment_filter in ["POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"]:
        komentar_qs = komentar_qs.filter(sentiment=sentiment_filter)

    # 1. Hitung total komentar terfilter
    total_komentar = komentar_qs.count()

    # 2. Hitung jumlah dan persentase sentimen
    positive_count = komentar_qs.filter(sentiment="POSITIVE").count()
    neutral_count = komentar_qs.filter(sentiment="NEUTRAL").count()
    negative_count = komentar_qs.filter(sentiment="NEGATIVE").count()

    positive_pct = pct(positive_count, total_komentar)
    neutral_pct = pct(neutral_count, total_komentar)
    negative_pct = pct(negative_count, total_komentar)

    # 3. Data Tiket
    tickets = Ticket.objects.all()
    total_tickets = tickets.count()
    open_tickets = tickets.filter(status__in=Ticket.OPEN_STATUSES).count()
    escalated = tickets.filter(escalated=True).count()
    sla_compliance = 100 - pct(escalated, total_tickets) if total_tickets else 100

    # 4. Ambil daftar komentar untuk tabel Mentions Terbaru (tampilkan hingga 50 data terbaru)
    komentar_list = komentar_qs.order_by("-dibuat_pada")[:50]

    # 5. Komentar kritis negatif
    critical_comments = komentar_qs.filter(sentiment="NEGATIVE").order_by("-dibuat_pada")[:5]

    # 6. Hitung topik paling banyak dibahas secara dinamis
    topics_list = []
    all_topics = Topic.objects.all()
    for t in all_topics:
        t_tickets = Ticket.objects.filter(topic=t).count()
        t_komentar = komentar_qs.filter(comment_text__icontains=t.name).count()
        total_topic = t_tickets + t_komentar
        if total_topic > 0:
            topics_list.append({
                "name": t.name.capitalize(),
                "count": total_topic,
                "pct": min(100, round((total_topic / (total_komentar or 1)) * 100)),
            })
    topics_list.sort(key=lambda x: x["count"], reverse=True)

    # 7. Data Tren Sentimen Harian untuk Chart.js (Line Chart)
    # Dikelompokkan via Python agar terbebas dari dependensi fungsi SQL CONVERT_TZ
    trend_comments = komentar_qs.values("dibuat_pada", "sentiment").order_by("dibuat_pada")
    dates_map = {}
    for item in trend_comments:
        d_val = item.get("dibuat_pada")
        if not d_val:
            continue
        d_str = d_val.strftime("%d %b")
        if d_str not in dates_map:
            dates_map[d_str] = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        sent = item.get("sentiment")
        if sent in dates_map[d_str]:
            dates_map[d_str][sent] += 1

    if dates_map:
        trend_labels = list(dates_map.keys())
        trend_positive = [dates_map[d]["POSITIVE"] for d in trend_labels]
        trend_neutral = [dates_map[d]["NEUTRAL"] for d in trend_labels]
        trend_negative = [dates_map[d]["NEGATIVE"] for d in trend_labels]
    else:
        trend_labels = ["Total Data"]
        trend_positive = [positive_count]
        trend_neutral = [neutral_count]
        trend_negative = [negative_count]

    has_filter = bool(q or (period and period != "all") or start_date_str or end_date_str or sentiment_filter)

    context = {
        # Total Mentions
        "total": total_komentar,
        # Tiket & SLA
        "open_tickets": open_tickets,
        "sla_compliance": sla_compliance,
        # Mentions & Kritis
        "komentar_list": komentar_list,
        "critical": critical_comments,
        # Sentimen
        "positive": positive_count,
        "neutral": neutral_count,
        "negative": negative_count,
        "positive_pct": positive_pct,
        "neutral_pct": neutral_pct,
        "negative_pct": negative_pct,
        # Topik
        "topics_list": topics_list,
        # Data Tren Chart JSON
        "trend_labels": json.dumps(trend_labels),
        "trend_positive": json.dumps(trend_positive),
        "trend_neutral": json.dumps(trend_neutral),
        "trend_negative": json.dumps(trend_negative),
        # State Filter
        "filter_label": filter_label or "Semua Waktu",
        "q": q,
        "period": period or "all",
        "start_date": start_date_str,
        "end_date": end_date_str,
        "sentiment_filter": sentiment_filter,
        "has_filter": has_filter,
    }

    return render(request, "core/dashboard.html", context)
