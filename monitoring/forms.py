from django import forms
from django.utils import timezone
from .models import SensorReading, LandslideIncident, MonitoringLocation, Alert


class ReadingForm(forms.ModelForm):
    """
    Field officer input form for landslide risk variables.
    Features robust validation preventing negative measurements and >100% soil saturation.
    """
    recorded_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        initial=timezone.now,
        help_text="Observation timestamp in Indian Standard Time (IST)"
    )

    class Meta:
        model = SensorReading
        fields = [
            'location',
            'rainfall_24h_mm',
            'rainfall_72h_mm',
            'soil_moisture_percent',
            'ground_vibration',
            'recorded_at'
        ]
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select select2-location'}),
            'rainfall_24h_mm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 85.5',
                'step': '0.1',
                'min': '0'
            }),
            'rainfall_72h_mm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 190.0',
                'step': '0.1',
                'min': '0'
            }),
            'soil_moisture_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 78.0',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'ground_vibration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 4.2',
                'step': '0.1',
                'min': '0'
            }),
        }

    def clean_rainfall_24h_mm(self):
        val = self.cleaned_data.get('rainfall_24h_mm')
        if val is not None and val < 0:
            raise forms.ValidationError("Rainfall cannot be a negative value. Enter 0 or above.")
        return val

    def clean_rainfall_72h_mm(self):
        val = self.cleaned_data.get('rainfall_72h_mm')
        if val is not None and val < 0:
            raise forms.ValidationError("72-hour cumulative rainfall cannot be negative.")
        return val

    def clean_soil_moisture_percent(self):
        val = self.cleaned_data.get('soil_moisture_percent')
        if val is not None:
            if val < 0.0 or val > 100.0:
                raise forms.ValidationError("Soil moisture saturation must be between 0.0% and 100.0%.")
        return val

    def clean_ground_vibration(self):
        val = self.cleaned_data.get('ground_vibration')
        if val is not None and val < 0:
            raise forms.ValidationError("Ground vibration velocity cannot be negative.")
        return val


class IncidentForm(forms.ModelForm):
    """
    Form to record an actual ground landslide event.
    """
    occurred_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        initial=timezone.now
    )

    class Meta:
        model = LandslideIncident
        fields = [
            'location',
            'occurred_at',
            'severity',
            'road_blocked',
            'description'
        ]
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'road_blocked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe extent of slope slide, estimated debris volume, affected infrastructure, and current response actions...'
            }),
        }


class AlertActionForm(forms.Form):
    """
    Form for DDMA officers to record operational actions taken when acknowledging or closing alerts.
    """
    action_note = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Record directives issued, personnel deployed, highway status, or clearance progress...'
        }),
        required=True,
        help_text="Detailed note for accountability and post-monsoon audit"
    )
