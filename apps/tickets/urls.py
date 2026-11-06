from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list, name="list"),
    path("new/", views.ticket_create, name="create"),
    path("<int:pk>/", views.ticket_detail, name="detail"),
    path("<int:pk>/status/", views.ticket_set_status, name="set_status"),
    path("<int:pk>/close/", views.ticket_close, name="close"),
    path("<int:pk>/update-result/", views.ticket_update_result, name="update_result"),
]