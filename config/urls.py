from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
import os
import socket

def db_check_view(request):
    db_conf = settings.DATABASES.get('default', {})
    host = db_conf.get('HOST')
    port = db_conf.get('PORT')
    user = db_conf.get('USER')
    name = db_conf.get('NAME')
    
    result = {
        'is_vercel': os.environ.get('VERCEL'),
        'configured_host': host,
        'configured_port': port,
        'configured_user': user,
        'configured_db': name,
    }
    
    # Test raw socket
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((host, int(port)))
        raw = s.recv(100)
        s.close()
        result['socket_raw_greeting'] = repr(raw)
    except Exception as se:
        result['socket_error'] = str(se)
        
    # Test Django connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        result['django_db_status'] = 'CONNECTED_SUCCESSFULLY'
        result['query_result'] = row
    except Exception as dbe:
        result['django_db_status'] = 'FAILED'
        result['django_db_error'] = str(dbe)
        
    return JsonResponse(result)

urlpatterns = [
    path("db-check/", db_check_view),
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