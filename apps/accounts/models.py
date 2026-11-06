from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "manager", "Manager"
        TEKNISI = "teknisi", "Teknisi"
        PIC = "pic", "PIC"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TEKNISI)
    unit = models.ForeignKey(
        "core.Unit", null=True, blank=True, on_delete=models.SET_NULL, related_name="members"
    )
    phone = models.CharField(max_length=30, blank=True)

    # Hak akses per role:
    #   Teknisi : Inbox, buat/kelola tiket, Monitoring, Pengaturan, semua tiket
    #   Manager : Dashboard, Analitik, melihat semua tiket
    #   PIC     : hanya tiket milik/unitnya
    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.TEKNISI

    @property
    def can_manage_inbox(self):
        return self.is_admin_role

    @property
    def can_view_analytics(self):
        return self.is_admin_role or self.role == self.Role.MANAGER