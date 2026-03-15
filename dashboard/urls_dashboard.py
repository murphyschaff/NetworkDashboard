from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("htmx/services/", views.dashboard_partial, name="dashboard_partial"),
]
