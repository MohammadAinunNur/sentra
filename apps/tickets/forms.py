from django import forms

from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "topic", "priority", "unit", "pic", "is_public"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class CloseTicketForm(forms.Form):
    resolution_note = forms.CharField(
        label="Catatan Keterangan Hasil Pekerjaan",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Jelaskan secara rinci tindakan penyelesaian dan keterangan hasil pekerjaan...",
            "class": "form-control",
            "style": "width: 100%; border-radius: 10px; border: 1px solid var(--line); padding: 12px; font-family: inherit;",
        }),
        required=True,
        help_text="Wajib diisi sebagai catatan keterangan hasil pekerjaan penanganan tiket ini."
    )
    work_result_image = forms.FileField(
        label="Dokumen Foto Hasil Pekerjaan",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/*,.pdf",
            "class": "form-control",
            "id": "id_work_result_image",
            "style": "width: 100%; border-radius: 10px; border: 1px dashed var(--blue); padding: 12px; background: #f8fafc;",
        }),
        help_text="Unggah dokumen foto atau berkas bukti hasil pekerjaan (format: JPG, PNG, WEBP, PDF)."
    )
    confirm = forms.BooleanField(
        label="Saya memastikan penanganan sudah selesai dan keterangan serta dokumen hasil pekerjaan sudah sesuai",
        required=True,
    )


class UpdateResultForm(forms.Form):
    resolution_note = forms.CharField(
        label="Catatan Keterangan Hasil Pekerjaan",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Perbarui catatan keterangan hasil pekerjaan...",
            "class": "form-control",
            "style": "width: 100%; border-radius: 10px; border: 1px solid var(--line); padding: 12px; font-family: inherit;",
        }),
        required=True,
    )
    work_result_image = forms.FileField(
        label="Dokumen Foto Hasil Pekerjaan (Opsional / Ganti)",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "accept": "image/*,.pdf",
            "class": "form-control",
            "style": "width: 100%; border-radius: 10px; border: 1px dashed var(--blue); padding: 12px; background: #f8fafc;",
        }),
        help_text="Pilih dokumen foto baru jika ingin memperbarui / mengganti foto hasil pekerjaan sebelumnya."
    )