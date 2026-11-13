from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.core.choices import DEFAULT_SLA_HOURS


def visible_tickets(user):
    """Teknisi/Manager melihat semua tiket; PIC melihat tiket miliknya, unitnya, atau tiket yang belum memiliki PIC."""
    from django.db.models import Q

    from .models import Ticket

    if user.can_view_analytics:
        return Ticket.objects.all()

    # Untuk pengguna dengan peran PIC:
    condition = Q(pic=user)
    if user.unit_id:
        condition |= Q(unit_id=user.unit_id)
    # Tiket yang belum ada PIC atau terisi bukan oleh PIC (agar PIC tetap dapat melihat & menanganinya)
    condition |= Q(pic__isnull=True) | ~Q(pic__role="pic")
    return Ticket.objects.filter(condition)


def sla_hours(priority):
    from apps.workflow.models import SLAConfig

    configured = SLAConfig.objects.filter(priority=priority, is_active=True).first()
    return configured.hours if configured else DEFAULT_SLA_HOURS.get(priority, 24)


def pick_pic(unit):
    """Pilih PIC aktif di unit tujuan. Jika unit belum memiliki PIC khusus, tugaskan ke PIC aktif mana saja di sistem."""
    if unit:
        pic = User.objects.filter(role=User.Role.PIC, unit=unit, is_active=True).first()
        if pic:
            return pic
    # Fallback jika unit belum memiliki PIC khusus atau unit kosong:
    return User.objects.filter(role=User.Role.PIC, is_active=True).first()


def create_ticket_from_mention(mention, *, unit=None, created_by=None, priority=None, title=None):
    from .models import Ticket

    priority = priority or mention.priority or "medium"
    ticket = Ticket.objects.create(
        mention=mention,
        title=title or f"{mention.get_channel_display()}: {mention.content[:80]}",
        description=mention.content,
        topic=mention.topic,
        priority=priority,
        unit=unit,
        pic=pick_pic(unit),
        created_by=created_by,
        due_at=timezone.now() + timedelta(hours=sla_hours(priority)),
    )
    ticket.add_history("Tiket dibuat", f"Dari mention {mention.author}", created_by)
    return ticket