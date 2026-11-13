from django.contrib import admin
from .models import MonitoringLocation, SensorReading, RiskPrediction, Alert, LandslideIncident


@admin.register(MonitoringLocation)
class MonitoringLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'district', 'slope_angle', 'soil_type', 'is_active', 'created_at')
    list_filter = ('state', 'is_active')
    search_fields = ('name', 'district', 'nearest_town_or_road', 'description')
    ordering = ('state', 'name')


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('location', 'rainfall_24h_mm', 'rainfall_72h_mm', 'soil_moisture_percent', 'ground_vibration', 'recorded_at', 'recorded_by')
    list_filter = ('location__state', 'recorded_at')
    search_fields = ('location__name',)
    date_hierarchy = 'recorded_at'


@admin.register(RiskPrediction)
class RiskPredictionAdmin(admin.ModelAdmin):
    list_display = ('location', 'risk_level', 'total_score', 'rainfall_score', 'soil_score', 'slope_score', 'vibration_score', 'predicted_at')
    list_filter = ('risk_level', 'location__state')
    search_fields = ('location__name', 'recommendation')
    date_hierarchy = 'predicted_at'


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('location', 'level', 'status', 'created_at', 'acknowledged_by', 'closed_by')
    list_filter = ('level', 'status', 'location__state')
    search_fields = ('location__name', 'title', 'message')
    date_hierarchy = 'created_at'


@admin.register(LandslideIncident)
class LandslideIncidentAdmin(admin.ModelAdmin):
    list_display = ('location', 'occurred_at', 'severity', 'road_blocked', 'reported_by')
    list_filter = ('severity', 'road_blocked', 'location__state')
    search_fields = ('location__name', 'description')
    date_hierarchy = 'occurred_at'
