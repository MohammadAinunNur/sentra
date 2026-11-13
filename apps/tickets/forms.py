from django import forms
from apps.accounts.models import User
from .models import Ticket


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "topic", "priority", "unit", "pic", "is_public"]
        widgets = {
            "title": forms.TextInput(attrs={"style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
            "description": forms.Textarea(attrs={"rows": 4, "style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
            "topic": forms.Select(attrs={"style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
            "priority": forms.Select(attrs={"style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
            "unit": forms.Select(attrs={"style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
            "pic": forms.Select(attrs={"style": "width: 100%; border-radius: 8px; border: 1px solid var(--line); padding: 8px 12px;"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Batasi pilihan PIC hanya kepada pengguna yang memiliki role PIC
        self.fields["pic"].queryset = User.objects.filter(role=User.Role.PIC, is_active=True)
        self.fields["pic"].required = False
        self.fields["pic"].empty_label = "-- Pilih Petugas PIC (Otomatis jika dikosongkan) --"
        self.fields["pic"].label = "Petugas PIC (Penanggung Jawab Lapangan)"
        self.fields["pic"].help_text = (
            "Hanya akun dengan peran PIC yang dapat dipilih. Jika dikosongkan, "
            "sistem akan otomatis memilih PIC aktif sesuai unit atau PIC yang tersedia."
        )
        self.fields["unit"].empty_label = "-- Pilih Unit Terkait --"


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