"""Pengambil komentar dari tiap platform.

Setiap collector menerima SocialConnection dan mengembalikan list dict:
{channel, external_id, author, content, posted_at, url, likes}
"""
import logging

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.core.choices import Channel

logger = logging.getLogger(__name__)

INSTAGRAM_MEDIA_LIMIT = 10  # periksa komentar pada 10 postingan terbaru tiap sinkronisasi


def _get_json(url, params, name):
    """GET + JSON dengan pesan error yang AMAN.

    Pesan error bawaan `requests` memuat URL lengkap (termasuk API key / token).
    Pesan itu akan tersimpan di log Monitoring, jadi di sini kita buat pesan sendiri
    tanpa URL.
    """
    try:
        resp = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        raise RuntimeError(f"{name}: gagal terhubung ({type(exc).__name__})") from None

    if resp.status_code != 200:
        try:
            err = resp.json().get("error", {})
            message = err.get("message") if isinstance(err, dict) else str(err)
        except ValueError:
            message = resp.text[:200]
        raise RuntimeError(f"{name} API {resp.status_code}: {message}")
    return resp.json()


def collect_youtube(conn):
    if not settings.YOUTUBE_API_KEY or not conn.account_id:
        logger.warning("YOUTUBE_API_KEY atau account_id (Channel ID) belum diisi.")
        return []

    payload = _get_json(
        "https://www.googleapis.com/youtube/v3/commentThreads",
        {
            "part": "snippet",
            "allThreadsRelatedToChannelId": conn.account_id,
            "maxResults": 50,
            "order": "time",
            "key": settings.YOUTUBE_API_KEY,
        },
        "YouTube",
    )

    items = []
    for item in payload.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        video_id = top.get("videoId", "")
        items.append(
            {
                "channel": Channel.YOUTUBE,
                "external_id": item["id"],
                "author": top.get("authorDisplayName", ""),
                "content": top.get("textOriginal") or top.get("textDisplay", ""),
                "posted_at": parse_datetime(top.get("publishedAt", "")) or timezone.now(),
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                "likes": top.get("likeCount", 0),
            }
        )
    return items


def collect_instagram(conn):
    """Instagram Graph API: ambil postingan terbaru, lalu komentar tiap postingan.

    Catatan dari dokumentasi Meta: endpoint komentar hanya mengembalikan komentar
    tingkat atas (bukan balasan), maksimal 50 per permintaan, dan tidak bisa
    difilter berdasarkan waktu. Komentar yang sudah ada otomatis dilewati oleh
    save_mentions().
    """
    if not settings.INSTAGRAM_ACCESS_TOKEN or not conn.account_id:
        logger.warning("INSTAGRAM_ACCESS_TOKEN atau account_id (ID akun Instagram Business) belum diisi.")
        return []

    base = f"https://{settings.INSTAGRAM_GRAPH_HOST}/{settings.INSTAGRAM_API_VERSION}"
    token = {"access_token": settings.INSTAGRAM_ACCESS_TOKEN}

    media_list = _get_json(
        f"{base}/{conn.account_id}/media",
        {"fields": "id,permalink", "limit": INSTAGRAM_MEDIA_LIMIT, **token},
        "Instagram",
    ).get("data", [])

    items = []
    for media in media_list:
        comments = _get_json(
            f"{base}/{media['id']}/comments",
            {"fields": "id,text,timestamp,username,like_count", "limit": 50, **token},
            "Instagram",
        ).get("data", [])
        for c in comments:
            items.append(
                {
                    "channel": Channel.INSTAGRAM,
                    "external_id": c["id"],
                    "author": c.get("username", ""),
                    "content": c.get("text", ""),
                    "posted_at": parse_datetime(c.get("timestamp", "")) or timezone.now(),
                    "url": media.get("permalink", ""),
                    "likes": c.get("like_count", 0),
                }
            )
    return items


COLLECTORS = {
    Channel.YOUTUBE: collect_youtube,
    Channel.INSTAGRAM: collect_instagram,
}


def save_mentions(items):
    """Simpan komentar baru; yang sudah ada (channel + external_id sama) dilewati."""
    from apps.inbox.models import Mention

    created = 0
    for data in items:
        if not data["content"].strip():
            continue  # komentar tanpa teks (mis. hanya stiker) tidak perlu dianalisis
        _, is_new = Mention.objects.get_or_create(
            channel=data["channel"],
            external_id=data["external_id"],
            defaults={k: data[k] for k in ("author", "content", "posted_at", "url", "likes")},
        )
        created += int(is_new)
    return created
