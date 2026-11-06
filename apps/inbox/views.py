from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from apps.core.models import Komentar
from apps.tickets.models import Ticket

@login_required
def inbox_list(request):
    # Mengambil seluruh data komentar dari database, diurutkan dari yang terbaru
    komentar_qs = Komentar.objects.all().order_by('-dibuat_pada')

    # Filter berdasarkan Sentimen jika dipilih di dropdown
    sentiment_filter = request.GET.get('sentiment')
    if sentiment_filter:
        komentar_qs = komentar_qs.filter(sentiment=sentiment_filter)

    # Filter berdasarkan Channel (jika nanti ada channel lain)
    channel_filter = request.GET.get('channel')
    if channel_filter:
        pass  # Sesuaikan jika field channel sudah ada di model Komentar

    # Hitung statistik untuk badge kartu atas secara dinamis
    total_all = Komentar.objects.count()
    total_ig = total_all  # Saat ini fokus utama pada Instagram
    total_positive = Komentar.objects.filter(sentiment='POSITIVE').count()
    total_neutral = Komentar.objects.filter(sentiment='NEUTRAL').count()
    total_negative = Komentar.objects.filter(sentiment='NEGATIVE').count()

    # Konfigurasi Paginator (10 data per halaman)
    paginator = Paginator(komentar_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pilihan untuk dropdown filter di template
    sentiments = [
        ('POSITIVE', 'Positif'),
        ('NEUTRAL', 'Netral'),
        ('NEGATIVE', 'Negatif'),
    ]
    channels = [
        ('instagram', 'Instagram'),
    ]

    context = {
        'page': page_obj,
        'total_all': total_all,
        'total_ig': total_ig,
        'total_positive': total_positive,
        'total_neutral': total_neutral,
        'total_negative': total_negative,
        'sentiments': sentiments,
        'channels': channels,
        'f': {
            'sentiment': sentiment_filter,
            'channel': channel_filter,
        }
    }
    return render(request, 'inbox/list.html', context)


@login_required
def inbox_detail(request, pk):
    # Mengambil satu data komentar spesifik berdasarkan Primary Key (pk) dari database
    mention = get_object_or_404(Komentar, pk=pk)
    
    # Ambil tiket terkait jika ada relasi
    tickets = Ticket.objects.filter(mention=mention) if hasattr(Ticket, 'mention') else []

    context = {
        'm': mention,
        'tickets': tickets,
    }
    return render(request, 'inbox/detail.html', context)