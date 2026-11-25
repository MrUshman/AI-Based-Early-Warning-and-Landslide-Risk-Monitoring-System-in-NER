from django.conf import settings
from django.db import models
from django.utils import timezone


class MonitoringLocation(models.Model):
    """A landslide-prone site / monitoring station in the North-East Region."""

    STATE_CHOICES = [
        ("Arunachal Pradesh", "Arunachal Pradesh"),
        ("Assam", "Assam"),
        ("Manipur", "Manipur"),
        ("Meghalaya", "Meghalaya"),
        ("Mizoram", "Mizoram"),
        ("Nagaland", "Nagaland"),
        ("Sikkim", "Sikkim"),
        ("Tripura", "Tripura"),
    ]
    SOIL_CHOICES = [
        ("clay", "Clay"),
        ("loamy", "Loamy"),
        ("sandy", "Sandy"),
        ("rocky", "Rocky / Fragmented"),
        ("silt", "Silt"),
    ]

    name = models.CharField(max_length=120, help_text="e.g. NH-10, km 32 (Rangpo side)")
    state = models.CharField(max_length=30, choices=STATE_CHOICES)
    district = models.CharField(max_length=80)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation_m = models.FloatField(default=0, help_text="Elevation in metres")
    slope_angle = models.FloatField(help_text="Slope angle in degrees (0-90)")
    soil_type = models.CharField(max_length=20, choices=SOIL_CHOICES, default="loamy")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["state", "name"]

    def __str__(self):
        return f"{self.name} ({self.district}, {self.state})"

    @property
    def latest_prediction(self):
        return self.predictions.first()

    @property
    def latest_reading(self):
        return self.readings.first()


class SensorReading(models.Model):
    """One set of field / weather observations for a location.

    In production these values would arrive from rain gauges, soil-moisture
    sensors and tiltmeters. Here they can be entered manually or seeded,
    which keeps the project easy to demonstrate.
    """

    location = models.ForeignKey(
        MonitoringLocation, on_delete=models.CASCADE, related_name="readings"
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    rainfall_24h_mm = models.FloatField(help_text="Rainfall in last 24 hours (mm)")
    rainfall_72h_mm = models.FloatField(help_text="Rainfall in last 72 hours (mm)")
    soil_moisture_pct = models.FloatField(help_text="Soil moisture (%)")
    ground_vibration = models.FloatField(
        default=0, help_text="Ground vibration / seismic activity (0-10 scale)"
    )
    temperature_c = models.FloatField(default=25)
    humidity_pct = models.FloatField(default=70)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.location.name} @ {self.recorded_at:%d %b %Y %H:%M}"


class RiskPrediction(models.Model):
    """Output of the AI risk engine for one reading."""

    LEVEL_CHOICES = [
        ("Low", "Low"),
        ("Moderate", "Moderate"),
        ("High", "High"),
        ("Critical", "Critical"),
    ]

    location = models.ForeignKey(
        MonitoringLocation, on_delete=models.CASCADE, related_name="predictions"
    )
    reading = models.OneToOneField(
        SensorReading, on_delete=models.CASCADE, related_name="prediction", null=True, blank=True
    )
    predicted_at = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField(help_text="0 (safe) to 100 (extremely dangerous)")
    risk_level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    rainfall_factor = models.FloatField(default=0)
    soil_factor = models.FloatField(default=0)
    slope_factor = models.FloatField(default=0)
    vibration_factor = models.FloatField(default=0)
    recommendation = models.TextField(blank=True)

    class Meta:
        ordering = ["-predicted_at"]

    def __str__(self):
        return f"{self.location.name}: {self.risk_level} ({self.risk_score:.0f}/100)"


class Alert(models.Model):
    """An early-warning alert raised when risk is High or Critical."""

    SEVERITY_CHOICES = RiskPrediction.LEVEL_CHOICES

    location = models.ForeignKey(
        MonitoringLocation, on_delete=models.CASCADE, related_name="alerts"
    )
    prediction = models.ForeignKey(
        RiskPrediction, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts"
    )
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    issued_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"[{self.severity}] {self.location.name} - {self.issued_at:%d %b %H:%M}"


class LandslideIncident(models.Model):
    """A past landslide, used as historical record / training context."""

    location_name = models.CharField(max_length=120)
    state = models.CharField(max_length=30, choices=MonitoringLocation.STATE_CHOICES)
    district = models.CharField(max_length=80, blank=True)
    occurred_on = models.DateField()
    description = models.TextField(blank=True)
    rainfall_before_mm = models.FloatField(null=True, blank=True, help_text="Rainfall before the event (mm)")
    damage_summary = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-occurred_on"]

    def __str__(self):
        return f"{self.location_name}, {self.state} - {self.occurred_on}"
