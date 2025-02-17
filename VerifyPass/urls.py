from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("check_pass/", views.check_pass, name="check_pass"),
    path("generate_passes/", views.generate_passes, name="generate_pass"),
    path("generate_pass/<str:pass_id>", views.generate_pass, name="generate_pass_with_id"),
    path("add_members/", views.add_members, name="add_members"),
]
