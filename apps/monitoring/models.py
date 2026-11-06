from django.db import models


class ActivityLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        FAILED = "failed", "Failed"

    service = models.CharField(max_length=60)
    activity = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.service}: {self.activity}"


def log(service, activity, status="success"):
    """Catat aktivitas sistem agar tampil di halaman Monitoring."""
    return ActivityLog.objects.create(service=service, activity=activity, status=status)