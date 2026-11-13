from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


NER_STATES = [
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Sikkim', 'Sikkim'),
    ('Tripura', 'Tripura'),
]

RISK_LEVEL_CHOICES = [
    ('LOW', 'Low'),
    ('MODERATE', 'Moderate'),
    ('HIGH', 'High'),
    ('CRITICAL', 'Critical'),
]

ALERT_LEVEL_CHOICES = [
    ('HIGH', 'High'),
    ('CRITICAL', 'Critical'),
]

ALERT_STATUS_CHOICES = [
    ('ACTIVE', 'Active'),
    ('ACKNOWLEDGED', 'Acknowledged'),
    ('CLOSED', 'Closed'),
]

INCIDENT_SEVERITY_CHOICES = [
    ('Minor', 'Minor'),
    ('Major', 'Major'),
    ('Severe', 'Severe'),
]


class MonitoringLocation(models.Model):
    """
    Represents a specific monitored landslide-prone slope or corridor in NER.
    """
    name = models.CharField(max_length=150, help_text="e.g. NH-10 km 32")
    state = models.CharField(max_length=50, choices=NER_STATES, help_text="One of the 8 NER states")
    district = models.CharField(max_length=100, help_text="District name")
    nearest_town_or_road = models.CharField(max_length=150, blank=True, help_text="Highway milestone or nearby town")
    latitude = models.FloatField(help_text="Latitude in decimal degrees")
    longitude = models.FloatField(help_text="Longitude in decimal degrees")
    slope_angle = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(90.0)],
        help_text="Slope steepness in degrees (feeds the risk engine)"
    )
    soil_type = models.CharField(max_length=100, help_text="e.g. Colluvium, Sandy Loam, Weathered Shale")
    description = models.TextField(blank=True, help_text="Geological history and past slide behavior")
    is_active = models.BooleanField(default=True, help_text="Soft on/off for monitoring")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['state', 'name']
        verbose_name = "Monitoring Location"
        verbose_name_plural = "Monitoring Locations"

    def __str__(self):
        return f"{self.name} ({self.state})"

    @property
    def latest_prediction(self):
        return self.predictions.order_by('-predicted_at').first()

    @property
    def latest_reading(self):
        return self.readings.order_by('-recorded_at').first()

    @property
    def current_risk_level(self):
        pred = self.latest_prediction
        return pred.risk_level if pred else 'LOW'

    @property
    def current_risk_score(self):
        pred = self.latest_prediction
        return pred.total_score if pred else 0.0

    @property
    def active_alert(self):
        return self.alerts.filter(status__in=['ACTIVE', 'ACKNOWLEDGED']).order_by('-created_at').first()

    @property
    def risk_badge_css(self):
        level = self.current_risk_level
        if level == 'CRITICAL':
            return 'bg-critical text-white'
        elif level == 'HIGH':
            return 'bg-high text-white'
        elif level == 'MODERATE':
            return 'bg-moderate text-dark'
        return 'bg-low text-white'

    @property
    def risk_color_hex(self):
        level = self.current_risk_level
        if level == 'CRITICAL':
            return '#DC2626'
        elif level == 'HIGH':
            return '#EA580C'
        elif level == 'MODERATE':
            return '#CA8A04'
        return '#16A34A'

    @property
    def risk_icon(self):
        level = self.current_risk_level
        if level == 'CRITICAL':
            return 'bi-exclamation-octagon-fill'
        elif level == 'HIGH':
            return 'bi-exclamation-triangle-fill'
        elif level == 'MODERATE':
            return 'bi-eye-fill'
        return 'bi-check-circle-fill'


class SensorReading(models.Model):
    """
    Sensor inputs collected for a location (rainfall, soil moisture, ground vibration).
    """
    location = models.ForeignKey(MonitoringLocation, on_delete=models.CASCADE, related_name='readings')
    rainfall_24h_mm = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Rainfall recorded in the last 24 hours (mm)"
    )
    rainfall_72h_mm = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Accumulated rainfall in the last 72 hours (mm)"
    )
    soil_moisture_percent = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Soil moisture saturation (0.0% to 100.0%)"
    )
    ground_vibration = models.FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Peak ground vibration velocity (mm/s)"
    )
    recorded_at = models.DateTimeField(default=timezone.now, help_text="Time of observation (IST)")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='readings')

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = "Sensor Reading"
        verbose_name_plural = "Sensor Readings"

    def __str__(self):
        return f"{self.location.name} @ {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"


class RiskPrediction(models.Model):
    """
    Saved outcome of the explainable risk engine for a given sensor reading.
    """
    location = models.ForeignKey(MonitoringLocation, on_delete=models.CASCADE, related_name='predictions')
    reading = models.OneToOneField(SensorReading, on_delete=models.CASCADE, related_name='prediction')
    rainfall_score = models.FloatField(help_text="Explainable score /40")
    soil_score = models.FloatField(help_text="Explainable score /25")
    slope_score = models.FloatField(help_text="Explainable score /20")
    vibration_score = models.FloatField(help_text="Explainable score /15")
    total_score = models.FloatField(help_text="Total risk index (0-100)")
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    recommendation = models.TextField(help_text="Auto-generated actionable plain-language advisory")
    predicted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-predicted_at']
        verbose_name = "Risk Prediction"
        verbose_name_plural = "Risk Predictions"

    def __str__(self):
        return f"{self.location.name} - {self.risk_level} ({self.total_score:.1f}/100)"

    @property
    def badge_css(self):
        if self.risk_level == 'CRITICAL':
            return 'bg-critical text-white'
        elif self.risk_level == 'HIGH':
            return 'bg-high text-white'
        elif self.risk_level == 'MODERATE':
            return 'bg-moderate text-dark'
        return 'bg-low text-white'

    @property
    def icon_class(self):
        if self.risk_level == 'CRITICAL':
            return 'bi-exclamation-octagon-fill'
        elif self.risk_level == 'HIGH':
            return 'bi-exclamation-triangle-fill'
        elif self.risk_level == 'MODERATE':
            return 'bi-eye-fill'
        return 'bi-check-circle-fill'


class Alert(models.Model):
    """
    Public safety / DDMA alert created automatically for HIGH and CRITICAL predictions.
    """
    location = models.ForeignKey(MonitoringLocation, on_delete=models.CASCADE, related_name='alerts')
    prediction = models.ForeignKey(RiskPrediction, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=ALERT_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=ALERT_STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(default=timezone.now)
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_alerts'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    action_taken_note = models.TextField(blank=True, help_text="Audit notes on actions executed")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self):
        return f"[{self.status}] {self.level} Alert - {self.location.name}"

    @property
    def badge_css(self):
        if self.level == 'CRITICAL':
            return 'bg-critical text-white'
        return 'bg-high text-white'


class LandslideIncident(models.Model):
    """
    Historical or live landslide events recorded on the ground.
    Used for verifying prediction calibration and post-disaster assessment.
    """
    location = models.ForeignKey(MonitoringLocation, on_delete=models.CASCADE, related_name='incidents')
    occurred_at = models.DateTimeField(default=timezone.now, help_text="Date and time of incident (IST)")
    severity = models.CharField(max_length=20, choices=INCIDENT_SEVERITY_CHOICES)
    road_blocked = models.BooleanField(default=False, help_text="Critical indicator for BRO/NHIDCL highway clearance")
    description = models.TextField(help_text="Observations, estimated debris volume, damage, clearance status")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']
        verbose_name = "Landslide Incident"
        verbose_name_plural = "Landslide Incidents"

    def __str__(self):
        return f"{self.severity} Incident at {self.location.name} on {self.occurred_at.strftime('%Y-%m-%d')}"
