from django.contrib import admin

from .models import Mention


@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = ("channel", "author", "sentiment", "priority", "is_handled", "posted_at")
    list_filter = ("channel", "sentiment", "priority", "is_handled")
    search_fields = ("content", "author")