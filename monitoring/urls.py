from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("locations/", views.location_list, name="location_list"),
    path("locations/add/", views.location_add, name="location_add"),
    path("locations/<int:pk>/", views.location_detail, name="location_detail"),
    path("locations/<int:pk>/fetch-weather/", views.fetch_live_weather, name="fetch_live_weather"),
    path("readings/add/", views.reading_add, name="reading_add"),
    path("predictions/", views.prediction_list, name="prediction_list"),
    path("alerts/", views.alert_list, name="alert_list"),
    path("alerts/<int:pk>/acknowledge/", views.alert_acknowledge, name="alert_acknowledge"),
    path("incidents/", views.incident_list, name="incident_list"),
    path("incidents/add/", views.incident_add, name="incident_add"),
    path("calculator/", views.risk_calculator, name="risk_calculator"),
    path("metrics/", views.model_metrics_view, name="model_metrics"),
    path("about/", views.about, name="about"),

    # REST API for IoT devices / simulation
    path("api/locations/", views.api_locations, name="api_locations"),
    path("api/readings/", views.api_create_reading, name="api_create_reading"),

    # Export data for disaster management
    path("export/alerts/", views.export_alerts_csv, name="export_alerts_csv"),
    path("export/readings/", views.export_readings_csv, name="export_readings_csv"),
]
