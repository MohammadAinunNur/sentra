from django.db import models

from apps.core.choices import Channel


class SocialConnection(models.Model):
    """Pengaturan koneksi ke satu platform media sosial."""

    class Status(models.TextChoices):
        CONNECTED = "connected", "Connected"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    channel = models.CharField(max_length=20, choices=Channel.choices, unique=True)
    account_name = models.CharField(max_length=120, help_text="Mis. @plnpaiton")
    account_id = models.CharField(
        max_length=120, blank=True,
        help_text="ID channel YouTube / ID akun Instagram Business",
    )
    sync_interval_minutes = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONNECTED)
    last_sync = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_channel_display()} ({self.account_name})"