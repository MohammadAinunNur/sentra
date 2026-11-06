from django.urls import path

from . import views

app_name = "configuration"

urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:tab>/", views.index, name="tab"),
]