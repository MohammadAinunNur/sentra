from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import LoginForm, RegistrationForm


def login_view(request):
    """View untuk otentikasi login pengguna dengan username atau email."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    next_url = request.GET.get("next") or request.POST.get("next") or settings.LOGIN_REDIRECT_URL

    if request.method == "POST":
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Pengaturan Remember Me
            if form.cleaned_data.get("remember_me"):
                request.session.set_expiry(1209600)  # 14 hari
            else:
                request.session.set_expiry(0)  # Sesi browser ditutup

            display_name = user.get_full_name() or user.username
            messages.success(request, f"Selamat datang kembali, {display_name}!")
            return redirect(next_url)
        else:
            messages.error(request, "Gagal masuk. Periksa kembali username/email dan kata sandi Anda.")
    else:
        initial_data = {}
        if "username" in request.GET:
            initial_data["username"] = request.GET.get("username", "")
        form = LoginForm(request=request, initial=initial_data)

    context = {
        "form": form,
        "next": next_url,
        "active_tab": "login",
    }
    return render(request, "accounts/login.html", context)


def register_view(request):
    """View untuk pendaftaran akun anggota tim baru SENTRA."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            display_name = user.get_full_name() or user.username
            messages.success(
                request,
                f"Pendaftaran berhasil! Akun untuk {display_name} telah aktif. Silakan masuk.",
            )
            return redirect(f"{reverse('accounts:login')}?username={user.username}")
        else:
            messages.error(
                request,
                "Mohon lengkapi formulir pendaftaran dengan data yang valid.",
            )
    else:
        form = RegistrationForm()

    context = {
        "form": form,
        "active_tab": "register",
    }
    return render(request, "accounts/register.html", context)


def logout_view(request):
    """View untuk logout pengguna."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Anda telah berhasil keluar dari sistem SENTRA.")
    return redirect("accounts:login")
