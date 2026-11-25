from django.contrib import admin

from .models import Alert, LandslideIncident, MonitoringLocation, RiskPrediction, SensorReading


@admin.register(MonitoringLocation)
class MonitoringLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "state", "slope_angle", "soil_type", "is_active")
    list_filter = ("state", "soil_type", "is_active")
    search_fields = ("name", "district")


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ("location", "recorded_at", "rainfall_24h_mm", "soil_moisture_pct", "ground_vibration")
    list_filter = ("location__state",)


@admin.register(RiskPrediction)
class RiskPredictionAdmin(admin.ModelAdmin):
    list_display = ("location", "risk_score", "risk_level", "predicted_at")
    list_filter = ("risk_level", "location__state")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("location", "severity", "issued_at", "is_acknowledged")
    list_filter = ("severity", "is_acknowledged")


@admin.register(LandslideIncident)
class LandslideIncidentAdmin(admin.ModelAdmin):
    list_display = ("location_name", "state", "occurred_on")
    list_filter = ("state",)
