from django.db import models

from apps.core.choices import PRIORITY_RANK, Channel, Priority, Sentiment


class Mention(models.Model):
    """Satu komentar/mention dari media sosial beserta hasil analisis AI."""

    channel = models.CharField(max_length=20, choices=Channel.choices)
    external_id = models.CharField(max_length=128)
    author = models.CharField(max_length=150, blank=True)
    content = models.TextField()
    url = models.URLField(blank=True)
    likes = models.PositiveIntegerField(default=0)
    posted_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    # Hasil analisis AI (diisi nanti oleh mesin AI)
    sentiment = models.CharField(max_length=10, choices=Sentiment.choices, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    topic = models.ForeignKey(
        "core.Topic", null=True, blank=True, on_delete=models.SET_NULL, related_name="mentions"
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, blank=True)
    ai_recommendation = models.TextField(blank=True)

    is_processed = models.BooleanField(default=False)
    is_handled = models.BooleanField(default=False)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-posted_at"]
        constraints = [
            models.UniqueConstraint(fields=["channel", "external_id"], name="uniq_mention_per_channel")
        ]

    def __str__(self):
        return f"[{self.channel}] {self.author}: {self.content[:40]}"

    @property
    def priority_rank(self):
        return PRIORITY_RANK.get(self.priority, 0)