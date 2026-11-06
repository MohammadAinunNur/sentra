from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("inbox/", include("apps.inbox.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("monitoring/", include("apps.monitoring.urls")),
    path("settings/", include("apps.configuration.urls")),
    
    # --- TAMBAHKAN BARIS INI UNTUK PIC ---
    path("pic/", include("apps.pic.urls")),
    # ------------------------------------
    
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if getattr(settings, 'STATICFILES_DIRS', None) else None)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)