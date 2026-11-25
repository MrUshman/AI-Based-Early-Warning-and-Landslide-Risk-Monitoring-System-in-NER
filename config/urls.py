from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=True)),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="monitoring/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("monitoring.urls")),
]

handler404 = "monitoring.views.custom_404_view"
handler500 = "monitoring.views.custom_500_view"

