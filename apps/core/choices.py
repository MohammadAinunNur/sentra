"""Pilihan bersama yang dipakai banyak app (sentimen, prioritas, channel)."""
from django.db import models


class Sentiment(models.TextChoices):
    POSITIVE = "positive", "Positif"
    NEUTRAL = "neutral", "Netral"
    NEGATIVE = "negative", "Negatif"


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class Channel(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    YOUTUBE = "youtube", "YouTube"
    TIKTOK = "tiktok", "TikTok"
    X = "x", "X (Twitter)"


PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# SLA bawaan (jam) bila belum diatur di menu Pengaturan
DEFAULT_SLA_HOURS = {"critical": 1, "high": 2, "medium": 8, "low": 24}