from django.urls import path
from . import views

urlpatterns = [
    path("", views.monitor, name="monitor"),
    path("htmx/services/", views.monitor_partial, name="monitor_partial"),
]
