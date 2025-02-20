from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login_view"),
    path("logout/", views.logout_view, name="logout_view"),
    path("check_pass/", views.check_pass, name="check_pass"),
    path("generate_passes/<str:category>", views.generate_passes_category, name="generate_pass"),
    path("generate_passes/", views.generate_passes, name="generate_passes"),
    path("generate_pass/<str:pass_id>", views.generate_pass, name="generate_pass_with_id"),
    path("add_members/", views.add_members, name="add_members"),
    path("generate_empty_passes/<int:count>", views.generate_empty_passes, name="generate_empty_passes"),
    path("empty_passes/", views.empty_passes, name="empty_passes"),
    path("show_checkins/", views.show_checkins, name="show_checkins"),
    path("show_external/", views.show_externals, name="show_externals")
]
