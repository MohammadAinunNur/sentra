from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db.models import Q
import re

from .models import User
from apps.core.models import Unit


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username atau Email",
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "Masukkan username atau email",
            "autofocus": True,
            "autocomplete": "username",
            "id": "id_username",
        })
    )
    password = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(attrs={
            "class": "auth-input",
            "placeholder": "Masukkan kata sandi",
            "autocomplete": "current-password",
            "id": "id_password",
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Ingat saya",
        initial=True,
        widget=forms.CheckboxInput(attrs={
            "class": "auth-checkbox",
            "id": "id_remember_me"
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            username_cleaned = username.strip()
            # Dukung login dengan username ATAU email
            user_obj = User.objects.filter(
                Q(username__iexact=username_cleaned) | Q(email__iexact=username_cleaned)
            ).first()

            target_username = user_obj.username if user_obj else username_cleaned
            self.user_cache = authenticate(self.request, username=target_username, password=password)

            if self.user_cache is None:
                raise ValidationError(
                    "Username/Email atau kata sandi tidak sesuai. Silakan periksa kembali.",
                    code="invalid_login"
                )
            elif not self.user_cache.is_active:
                raise ValidationError(
                    "Akun Anda berstatus nonaktif. Silakan hubungi Administrator SENTRA.",
                    code="inactive"
                )

        return cleaned_data

    def get_user(self):
        return self.user_cache


class RegistrationForm(forms.ModelForm):
    full_name = forms.CharField(
        label="Nama Lengkap",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "Contoh: Budi Pratama",
            "autocomplete": "name",
            "id": "id_full_name",
        })
    )
    username = forms.CharField(
        label="Username",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "budi_pratama (min. 3 karakter)",
            "autocomplete": "username",
            "id": "id_reg_username",
        })
    )
    email = forms.EmailField(
        label="Email Kerja",
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "auth-input",
            "placeholder": "budi@perusahaan.com",
            "autocomplete": "email",
            "id": "id_reg_email",
        })
    )
    phone = forms.CharField(
        label="Nomor Telepon / WhatsApp",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "081234567890",
            "autocomplete": "tel",
            "id": "id_reg_phone",
        })
    )
    role = forms.ChoiceField(
        label="Peran Akun",
        choices=User.Role.choices,
        initial=User.Role.TEKNISI,
        widget=forms.RadioSelect(attrs={"class": "role-radio-hidden"})
    )
    unit = forms.ModelChoiceField(
        label="Unit Kerja (Opsional)",
        queryset=Unit.objects.all(),
        required=False,
        empty_label="-- Pilih Unit Kerja Terkait --",
        widget=forms.Select(attrs={
            "class": "auth-select",
            "id": "id_reg_unit"
        })
    )
    password = forms.CharField(
        label="Kata Sandi",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "auth-input",
            "placeholder": "Minimal 8 karakter kombinasi",
            "autocomplete": "new-password",
            "id": "id_reg_password",
        })
    )
    password_confirm = forms.CharField(
        label="Konfirmasi Kata Sandi",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            "class": "auth-input",
            "placeholder": "Ulangi kata sandi Anda",
            "autocomplete": "new-password",
            "id": "id_reg_password_confirm",
        })
    )
    terms = forms.BooleanField(
        label="Saya menyetujui Ketentuan Penggunaan dan Kebijakan Keamanan Data SENTRA.",
        required=True,
        widget=forms.CheckboxInput(attrs={
            "class": "auth-checkbox",
            "id": "id_terms"
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "phone", "role", "unit"]

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if not username:
            raise ValidationError("Username wajib diisi.")
        if len(username) < 3:
            raise ValidationError("Username minimal harus 3 karakter.")
        if not re.match(r"^[a-zA-Z0-9_.]+$", username):
            raise ValidationError("Username hanya boleh huruf, angka, titik (.), atau garis bawah (_).")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username ini telah digunakan. Silakan gunakan username lain.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email ini telah terdaftar. Silakan gunakan email lain atau masuk.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                self.add_error("password_confirm", "Konfirmasi kata sandi tidak cocok dengan kata sandi.")
            elif len(password) < 8:
                self.add_error("password", "Kata sandi harus minimal 8 karakter.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get("full_name", "").strip()
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

