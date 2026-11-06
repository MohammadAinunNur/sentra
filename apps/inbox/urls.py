from django.urls import path
from apps.inbox import views

app_name = 'inbox'

urlpatterns = [
    path('', views.inbox_list, name='list'),
    path('<int:pk>/', views.inbox_detail, name='detail'),
]