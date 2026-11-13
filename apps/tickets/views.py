from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import access_required
from apps.core.choices import Priority
from apps.inbox.models import Mention

from .forms import CloseTicketForm, TicketForm, UpdateResultForm
from .models import Ticket
from .services import pick_pic, sla_hours, visible_tickets


@login_required
def ticket_list(request):
    qs = visible_tickets(request.user).select_related("pic", "topic", "unit", "mention").distinct()
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    q = request.GET.get("q", "")
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if q:
        qs = qs.filter(title__icontains=q)

    # Hitung statistik ringkasan kartu atas secara dinamis dari database
    base_qs = visible_tickets(request.user)
    total_tickets = base_qs.count()
    open_count = base_qs.filter(status="open").count()
    in_progress_count = base_qs.filter(status="in_progress").count()
    resolved_count = base_qs.filter(status="resolved").count()

    params = request.GET.copy()
    params.pop("page", None)
    
    context = {
        "page": Paginator(qs, 20).get_page(request.GET.get("page")),
        "querystring": params.urlencode(),
        "statuses": Ticket.Status.choices,
        "priorities": Priority.choices,
        "f": {"status": status, "priority": priority, "q": q},
        # Kirim variabel statistik
        "total_tickets": total_tickets,
        "open_count": open_count,
        "in_progress_count": in_progress_count,
        "resolved_count": resolved_count,
    }
    return render(request, "tickets/list.html", context)


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(visible_tickets(request.user).distinct(), pk=pk)
    close_form = CloseTicketForm()
    update_form = UpdateResultForm(initial={"resolution_note": ticket.resolution_note})
    return render(
        request,
        "tickets/detail.html",
        {
            "t": ticket,
            "history": ticket.history.select_related("actor"),
            "close_form": close_form,
            "update_form": update_form,
        },
    )


from apps.core.models import Komentar  # Pastikan import ini ada

@access_required("can_manage_inbox")
def ticket_create(request):
    mention = None
    initial = {}
    if request.GET.get("mention"):
        # Mengambil dari model Komentar lokal
        mention = get_object_or_404(Komentar, pk=request.GET["mention"])
        initial = {
            "title": f"Keluhan Instagram dari @{mention.username}",
            "description": mention.comment_text,
            "priority": "medium",  # Sesuaikan dengan field sentiment jika ingin otomatis (misal: negatif jadi high)
        }

    form = TicketForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        ticket = form.save(commit=False)
        ticket.mention = mention
        ticket.created_by = request.user
        # Pastikan PIC terisi dengan pengguna ber-role PIC yang valid
        if not ticket.pic or getattr(ticket.pic, "role", None) != "pic":
            ticket.pic = pick_pic(ticket.unit)
        ticket.due_at = timezone.now() + timedelta(hours=sla_hours(ticket.priority))
        ticket.save()
        ticket.add_history("Tiket dibuat", actor=request.user)
        messages.success(request, f"Tiket {ticket.code} berhasil dibuat.")
        return redirect("tickets:detail", pk=ticket.pk)
    return render(request, "tickets/form.html", {"form": form, "mention": mention})


@login_required
@require_POST
def ticket_set_status(request, pk):
    ticket = get_object_or_404(visible_tickets(request.user).distinct(), pk=pk)
    new_status = request.POST.get("status")
    note = request.POST.get("note", "").strip()
    attachment = request.FILES.get("attachment")
    allowed = {Ticket.Status.IN_PROGRESS, Ticket.Status.WAITING}
    if new_status in allowed:
        ticket.status = new_status
        ticket.save(update_fields=["status", "updated_at"])
        action_text = f"Status diubah ke {ticket.get_status_display()}"
        ticket.add_history(action_text, note=note, actor=request.user, attachment=attachment)
        messages.success(request, f"Status tiket diperbarui menjadi {ticket.get_status_display()}.")
    elif note or attachment:
        ticket.add_history("Catatan Progres Pekerjaan", note=note, actor=request.user, attachment=attachment)
        messages.success(request, "Catatan pekerjaan berhasil ditambahkan ke riwayat tiket.")
    return redirect("tickets:detail", pk=pk)


@login_required
def ticket_close(request, pk):
    ticket = get_object_or_404(visible_tickets(request.user).distinct(), pk=pk)
    form = CloseTicketForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        ticket.status = Ticket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.resolution_note = form.cleaned_data["resolution_note"]
        if form.cleaned_data.get("work_result_image"):
            ticket.work_result_image = form.cleaned_data["work_result_image"]
        ticket.save()
        ticket.add_history(
            "Tiket selesai",
            note=ticket.resolution_note,
            actor=request.user,
            attachment=ticket.work_result_image,
        )
        messages.success(request, f"Tiket {ticket.code} berhasil diselesaikan dengan catatan dan dokumen hasil pekerjaan.")
        return redirect("tickets:detail", pk=pk)
    return render(request, "tickets/close.html", {"t": ticket, "form": form})


@login_required
@require_POST
def ticket_update_result(request, pk):
    ticket = get_object_or_404(visible_tickets(request.user).distinct(), pk=pk)
    form = UpdateResultForm(request.POST, request.FILES)
    if form.is_valid():
        ticket.resolution_note = form.cleaned_data["resolution_note"]
        if form.cleaned_data.get("work_result_image"):
            ticket.work_result_image = form.cleaned_data["work_result_image"]
        ticket.save()
        ticket.add_history(
            "Hasil pekerjaan diperbarui",
            note=ticket.resolution_note,
            actor=request.user,
            attachment=ticket.work_result_image,
        )
        messages.success(request, "Catatan keterangan dan dokumen foto hasil pekerjaan berhasil diperbarui.")
    else:
        messages.error(request, "Gagal memperbarui hasil pekerjaan. Pastikan input catatan terisi.")
    return redirect("tickets:detail", pk=pk)