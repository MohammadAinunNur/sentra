from django.contrib import admin

from .models import Ticket, TicketHistory


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("action", "note", "actor", "attachment", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "priority", "status", "pic", "due_at", "escalated")
    list_filter = ("status", "priority", "escalated")
    search_fields = ("code", "title", "resolution_note")
    inlines = [TicketHistoryInline]
    fieldsets = (
        ("Informasi Tiket", {"fields": ("code", "title", "description", "topic", "unit", "priority", "status", "pic", "is_public")}),
        ("SLA & Eskalasi", {"fields": ("due_at", "reminded", "escalated")}),
        ("Hasil Pekerjaan", {"fields": ("resolved_at", "resolution_note", "work_result_image")}),
    )
    readonly_fields = ("code",)