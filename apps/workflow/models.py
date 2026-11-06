from django.db import models

from apps.core.choices import PRIORITY_RANK, Priority, Sentiment


class WorkflowRule(models.Model):
    """Aturan IF-THEN. Dievaluasi berurutan (order); rule pertama yang cocok dijalankan."""

    name = models.CharField(max_length=120)
    # Kondisi (IF) - kosong = berlaku untuk semua
    sentiment = models.CharField(max_length=10, choices=Sentiment.choices, blank=True)
    min_priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    topic = models.ForeignKey("core.Topic", null=True, blank=True, on_delete=models.SET_NULL)
    # Aksi (THEN)
    create_ticket = models.BooleanField(default=True)
    assign_unit = models.ForeignKey("core.Unit", null=True, blank=True, on_delete=models.SET_NULL)
    send_notification = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    def matches(self, mention):
        if self.sentiment and mention.sentiment != self.sentiment:
            return False
        if PRIORITY_RANK.get(mention.priority, 0) < PRIORITY_RANK[self.min_priority]:
            return False
        if self.topic_id and mention.topic_id != self.topic_id:
            return False
        return True


class SLAConfig(models.Model):
    priority = models.CharField(max_length=10, choices=Priority.choices, unique=True)
    hours = models.PositiveIntegerField(help_text="Batas waktu penanganan (jam)")
    escalate_to = models.CharField(max_length=60, blank=True, help_text="Mis. Manager / Supervisor / PIC")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.priority}: {self.hours} jam"


class EscalationRule(models.Model):
    class Condition(models.TextChoices):
        NEAR_SLA = "near_sla", "80% dari SLA tercapai"
        OVERDUE = "overdue", "SLA terlewati"
        CRITICAL = "critical", "Prioritas Critical"

    class Action(models.TextChoices):
        REMINDER = "reminder", "Kirim reminder ke PIC"
        ESCALATE = "escalate", "Escalate ke Supervisor"
        NOTIFY_MANAGER = "notify_manager", "Notify Manager"

    condition = models.CharField(max_length=20, choices=Condition.choices, unique=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    channels = models.CharField(max_length=80, default="email,in_app", help_text="Pisahkan dengan koma")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_condition_display()} -> {self.get_action_display()}"