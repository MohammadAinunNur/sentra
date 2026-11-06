"""Pengiriman notifikasi.

- email    : dikirim lewat Django (console saat uji, SMTP bila dikonfigurasi di .env)
- in_app   : dicatat ke log Monitoring (belum ada kotak notifikasi sendiri)
- whatsapp : BELUM terhubung; dicatat sebagai "dilewati" agar log tidak menyesatkan
"""
from django.conf import settings
from django.core.mail import send_mail

from apps.monitoring.models import log


def notify(recipient, subject, channels=("in_app",)):
    target = getattr(recipient, "username", None) or "belum ada PIC"
    done, skipped = [], []

    if "email" in channels:
        address = getattr(recipient, "email", "")
        if not address:
            skipped.append("email (penerima tanpa alamat email)")
        else:
            try:
                send_mail(
                    subject,
                    f"{subject}\n\nBuka SENTRA untuk menindaklanjuti.",
                    settings.DEFAULT_FROM_EMAIL,
                    [address],
                )
                done.append("email")
            except Exception as exc:
                log("Notification", f"Email ke {target} gagal: {type(exc).__name__}", "failed")

    if "in_app" in channels:
        done.append("in_app")
    if "whatsapp" in channels:
        skipped.append("whatsapp (belum terhubung)")

    message = f"{subject} -> {target} via {', '.join(done) or '-'}"
    if skipped:
        message += f" | dilewati: {', '.join(skipped)}"
    log("Notification", message, "warning" if skipped else "success")