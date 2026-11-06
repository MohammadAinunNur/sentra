from django.db import models
from apps.accounts.models import User

from django.db import models

class Komentar(models.Model):
    post_id = models.CharField(max_length=100, blank=True, null=True)
    caption = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    comment_text = models.TextField()
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    
    # Tambahkan field sentimen di sini
    sentiment = models.CharField(
        max_length=20, 
        choices=[
            ('POSITIVE', 'Positif'),
            ('NEUTRAL', 'Netral'),
            ('NEGATIVE', 'Negatif'),
            ('MIXED', 'Campuran')
        ],
        default='NEUTRAL'
    )

    def __str__(self):
        return f"@{self.username}: {self.comment_text[:30]}"

class Unit(models.Model):
    """Unit kerja tujuan penugasan tiket (mis. Unit 9 - Operasi)."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Topic(models.Model):
    """Topik/isu hasil klasifikasi AI (mis. Gangguan Listrik, Lingkungan)."""

    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Keyword(models.Model):
    """Kata kunci yang dipantau, opsional dikaitkan dengan topik."""

    word = models.CharField(max_length=80, unique=True)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.word