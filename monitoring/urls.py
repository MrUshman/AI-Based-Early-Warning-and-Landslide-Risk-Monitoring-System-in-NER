from django.urls import path
from . import views

urlpatterns = [
    # Public views
    path('', views.public_dashboard, name='home'),
    path('locations/', views.locations_list, name='locations_list'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('alerts/', views.alerts_list, name='alerts_list'),
    path('alerts/<int:pk>/', views.alert_detail, name='alert_detail'),
    path('incidents/', views.incidents_list, name='incidents_list'),
    path('safety/', views.safety_guidance, name='safety_guidance'),
    path('about/', views.about_agencies, name='about_agencies'),

    # Operational actions & logged-in views
    path('alerts/<int:pk>/acknowledge/', views.alert_acknowledge, name='alert_acknowledge'),
    path('alerts/<int:pk>/close/', views.alert_close, name='alert_close'),
    path('readings/add/', views.reading_add, name='reading_add'),
    path('predictions/', views.predictions_list, name='predictions_list'),
    path('incidents/add/', views.incident_add, name='incident_add'),
    path('officer/', views.officer_dashboard, name='officer_dashboard'),

    # Interactive APIs for Map, Charts & Live Scoring preview
    path('api/locations-geojson/', views.api_locations_geojson, name='api_locations_geojson'),
    path('api/location/<int:pk>/trend/', views.api_location_trend, name='api_location_trend'),
    path('api/calculate-risk-preview/', views.api_calculate_preview, name='api_calculate_preview'),
]
