from django import forms

from .models import LandslideIncident, MonitoringLocation, SensorReading


class LocationForm(forms.ModelForm):
    class Meta:
        model = MonitoringLocation
        fields = ["name", "state", "district", "latitude", "longitude",
                  "elevation_m", "slope_angle", "soil_type", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ReadingForm(forms.ModelForm):
    class Meta:
        model = SensorReading
        fields = ["location", "rainfall_24h_mm", "rainfall_72h_mm",
                  "soil_moisture_pct", "ground_vibration", "temperature_c", "humidity_pct"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class IncidentForm(forms.ModelForm):
    class Meta:
        model = LandslideIncident
        fields = ["location_name", "state", "district", "occurred_on",
                  "description", "rainfall_before_mm", "damage_summary"]
        widgets = {"occurred_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class RiskCalculatorForm(forms.Form):
    rainfall_24h_mm = forms.FloatField(label="Rainfall in last 24 hours (mm)", initial=80)
    rainfall_72h_mm = forms.FloatField(label="Rainfall in last 72 hours (mm)", initial=180)
    soil_moisture_pct = forms.FloatField(label="Soil moisture (%)", initial=65)
    slope_angle = forms.FloatField(label="Slope angle (degrees)", initial=35)
    ground_vibration = forms.FloatField(label="Ground vibration (0-10)", initial=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
