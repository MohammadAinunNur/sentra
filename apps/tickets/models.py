from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.choices import Priority


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        WAITING = "waiting", "Waiting Response"
        RESOLVED = "resolved", "Resolved"

    OPEN_STATUSES = (Status.OPEN, Status.IN_PROGRESS, Status.WAITING)

    code = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    mention = models.ForeignKey(
        "core.Komentar", null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    topic = models.ForeignKey("core.Topic", null=True, blank=True, on_delete=models.SET_NULL)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    unit = models.ForeignKey("core.Unit", null=True, blank=True, on_delete=models.SET_NULL)
    pic = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_tickets",
    )
    is_public = models.BooleanField(default=False, help_text="Tampilkan ke pengguna terkait")

    # SLA & eskalasi
    due_at = models.DateTimeField(null=True, blank=True)
    reminded = models.BooleanField(default=False)
    escalated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True, verbose_name="Catatan Keterangan Hasil Pekerjaan")
    work_result_image = models.FileField(
        upload_to="tickets/results/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Dokumen Foto Hasil Pekerjaan",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code or '#'} {self.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.code:
            self.code = f"TKT-{timezone.now():%Y}-{self.pk:04d}"
            Ticket.objects.filter(pk=self.pk).update(code=self.code)

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    @property
    def is_overdue(self):
        return bool(self.due_at and self.is_open and timezone.now() > self.due_at)

    @property
    def is_image(self):
        if not self.work_result_image:
            return False
        ext = self.work_result_image.name.lower().rsplit(".", 1)[-1]
        return ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]

    def add_history(self, action, note="", actor=None, attachment=None):
        return self.history.create(action=action, note=note, actor=actor, attachment=attachment)


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    action = models.CharField(max_length=120)
    note = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="tickets/history/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Dokumen Foto Lampiran",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "ticket history"

    @property
    def is_image(self):
        if not self.attachment:
            return False
        ext = self.attachment.name.lower().rsplit(".", 1)[-1]
        return ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]