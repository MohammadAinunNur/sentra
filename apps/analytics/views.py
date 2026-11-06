import json
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from apps.core.models import Komentar


@login_required
def analytics_index(request):
    # Filter hari (default 30 hari)
    try:
        days = int(request.GET.get('days', 30))
    except ValueError:
        days = 30

    day_options = [7, 14, 30, 90]
    now = timezone.now()
    start_date = now - timedelta(days=days)

    # Base QuerySet berdasarkan rentang waktu
    qs = Komentar.objects.filter(dibuat_pada__gte=start_date)

    # 1. Total Sentimen
    total = qs.count()
    positive = qs.filter(sentiment='POSITIVE').count()
    neutral = qs.filter(sentiment='NEUTRAL').count()
    negative = qs.filter(sentiment='NEGATIVE').count()

    # Persentase
    pos_pct = round((positive / total * 100), 1) if total > 0 else 0
    neu_pct = round((neutral / total * 100), 1) if total > 0 else 0
    neg_pct = round((negative / total * 100), 1) if total > 0 else 0

    # 2. Data Tren Harian untuk Chart.js
    trend_qs = (
        qs.annotate(date=TruncDate('dibuat_pada'))
        .values('date', 'sentiment')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Grouping tanggal untuk Line Chart
    dates_map = {}
    for item in trend_qs:
        d_str = item['date'].strftime('%d %b') if item['date'] else ''
        if not d_str:
            continue
        if d_str not in dates_map:
            dates_map[d_str] = {'POSITIVE': 0, 'NEUTRAL': 0, 'NEGATIVE': 0}
        dates_map[d_str][item['sentiment']] = item['count']

    chart_labels = list(dates_map.keys())
    chart_pos = [dates_map[d]['POSITIVE'] for d in chart_labels]
    chart_neu = [dates_map[d]['NEUTRAL'] for d in chart_labels]
    chart_neg = [dates_map[d]['NEGATIVE'] for d in chart_labels]

    # 3. Mention Terbaru Instagram
    top_mentions = qs.order_by('-dibuat_pada')[:5]

    context = {
        'days': days,
        'day_options': day_options,
        'total': total,
        'positive': positive,
        'neutral': neutral,
        'negative': negative,
        'pos_pct': pos_pct,
        'neu_pct': neu_pct,
        'neg_pct': neg_pct,
        'top_mentions': top_mentions,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_pos_json': json.dumps(chart_pos),
        'chart_neu_json': json.dumps(chart_neu),
        'chart_neg_json': json.dumps(chart_neg),
    }
    return render(request, 'analytics/index.html', context)