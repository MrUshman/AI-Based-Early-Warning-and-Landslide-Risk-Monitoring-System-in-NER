"""
URL configuration for landslide_ews project.
"""
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "NER Landslide Early Warning System Administration"
admin.site.site_title = "NER Landslide EWS Admin"
admin.site.index_title = "Disaster Management & Slope Monitoring Console"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('monitoring.urls')),
]
