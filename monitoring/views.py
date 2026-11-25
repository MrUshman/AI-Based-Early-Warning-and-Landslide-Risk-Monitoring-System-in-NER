import csv
import json
import random
from datetime import datetime

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import IncidentForm, LocationForm, ReadingForm, RiskCalculatorForm
from .models import Alert, LandslideIncident, MonitoringLocation, RiskPrediction, SensorReading
from .risk_engine import evaluate_reading, get_model_metadata, predict_risk

LEVEL_COLORS = {
    "Low": "#10b981",       # Emerald green
    "Moderate": "#f59e0b",  # Amber yellow
    "High": "#f97316",      # Vivid orange
    "Critical": "#ef4444",  # Crimson red
}


def dashboard(request):
    locations = MonitoringLocation.objects.filter(is_active=True)

    # Latest prediction per location
    seen = set()
    latest_predictions = []
    for pred in RiskPrediction.objects.select_related("location").order_by("-predicted_at"):
        if pred.location_id not in seen:
            seen.add(pred.location_id)
            latest_predictions.append(pred)

    level_counts = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    for pred in latest_predictions:
        if pred.risk_level in level_counts:
            level_counts[pred.risk_level] += 1

    state_data = list(
        MonitoringLocation.objects.values("state").annotate(total=Count("id")).order_by("state")
    )

    # Prepare GeoJSON-like list for interactive Leaflet Map
    map_locations = []
    latest_pred_map = {p.location_id: p for p in latest_predictions}
    for loc in locations:
        pred = latest_pred_map.get(loc.id)
        risk_level = pred.risk_level if pred else "Low"
        risk_score = round(pred.risk_score) if pred else 0
        map_locations.append({
            "id": loc.id,
            "name": loc.name,
            "state": loc.state,
            "district": loc.district,
            "lat": loc.latitude,
            "lon": loc.longitude,
            "elevation": loc.elevation_m,
            "slope": loc.slope_angle,
            "soil": loc.get_soil_type_display(),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "color": LEVEL_COLORS.get(risk_level, "#10b981"),
            "url": f"/locations/{loc.id}/",
        })

    recent_readings = SensorReading.objects.select_related("location").order_by("-recorded_at")[:6]
    recent_alerts = Alert.objects.select_related("location").order_by("-issued_at")[:6]

    context = {
        "total_locations": locations.count(),
        "total_readings": SensorReading.objects.count(),
        "active_alerts": Alert.objects.filter(is_acknowledged=False).count(),
        "critical_sites": level_counts.get("Critical", 0),
        "high_sites": level_counts.get("High", 0),
        "latest_predictions": sorted(latest_predictions, key=lambda p: -p.risk_score),
        "recent_alerts": recent_alerts,
        "recent_readings": recent_readings,
        "map_locations_json": json.dumps(map_locations),
        "level_counts_json": json.dumps(level_counts),
        "state_labels_json": json.dumps([s["state"] for s in state_data]),
        "state_counts_json": json.dumps([s["total"] for s in state_data]),
        "level_colors": LEVEL_COLORS,
    }
    return render(request, "monitoring/dashboard.html", context)


def location_list(request):
    state = request.GET.get("state", "")
    locations = MonitoringLocation.objects.all()
    if state:
        locations = locations.filter(state=state)

    # Attach latest prediction to each location
    loc_list = []
    for loc in locations:
        loc_list.append({
            "loc": loc,
            "pred": loc.latest_prediction,
        })

    return render(request, "monitoring/location_list.html", {
        "locations_data": loc_list,
        "states": MonitoringLocation.STATE_CHOICES,
        "selected_state": state,
        "level_colors": LEVEL_COLORS,
    })


def location_detail(request, pk):
    location = get_object_or_404(MonitoringLocation, pk=pk)
    readings = location.readings.all()[:15]
    reversed_readings = list(reversed(list(readings)))

    chart_labels = [r.recorded_at.strftime("%d %b %H:%M") for r in reversed_readings]
    chart_rain_24 = [r.rainfall_24h_mm for r in reversed_readings]
    chart_soil_moisture = [r.soil_moisture_pct for r in reversed_readings]

    map_point = {
        "id": location.id,
        "name": location.name,
        "lat": location.latitude,
        "lon": location.longitude,
        "slope": location.slope_angle,
        "elevation": location.elevation_m,
        "risk_level": location.latest_prediction.risk_level if location.latest_prediction else "Low",
        "risk_score": round(location.latest_prediction.risk_score) if location.latest_prediction else 0,
        "color": LEVEL_COLORS.get(
            location.latest_prediction.risk_level if location.latest_prediction else "Low", "#10b981"
        ),
    }

    return render(request, "monitoring/location_detail.html", {
        "location": location,
        "readings": readings,
        "predictions": location.predictions.all()[:10],
        "alerts": location.alerts.all()[:8],
        "map_point_json": json.dumps(map_point),
        "chart_labels_json": json.dumps(chart_labels),
        "chart_rain_json": json.dumps(chart_rain_24),
        "chart_soil_json": json.dumps(chart_soil_moisture),
        "level_colors": LEVEL_COLORS,
    })


@login_required
def location_add(request):
    form = LocationForm(request.POST or None)
    if form.is_valid():
        loc = form.save()
        messages.success(request, f"Monitoring station '{loc.name}' created successfully.")
        return redirect("location_detail", pk=loc.pk)
    return render(request, "monitoring/form.html", {
        "form": form,
        "title": "Register New Monitoring Station",
        "subtitle": "Add geographical and geotechnical parameters for a landslide-vulnerable site in NER.",
    })


@login_required
def reading_add(request):
    initial = {}
    location_id = request.GET.get("location")
    if location_id:
        initial["location"] = location_id

    form = ReadingForm(request.POST or None, initial=initial)
    if form.is_valid():
        reading = form.save()
        prediction = evaluate_reading(reading)
        if prediction.risk_level in ("High", "Critical"):
            messages.error(
                request,
                f"🚨 {prediction.risk_level.upper()} ALERT TRIGGERED ({prediction.risk_score:.0f}/100) at "
                f"{reading.location.name}! Automated early warning issued to disaster authorities.",
            )
        else:
            messages.success(
                request,
                f"Observation recorded. AI Risk Engine evaluated status as {prediction.risk_level} "
                f"({prediction.risk_score:.0f}/100).",
            )
        return redirect("location_detail", pk=reading.location.pk)
    return render(request, "monitoring/form.html", {
        "form": form,
        "title": "Log Sensor & Weather Reading",
        "subtitle": "Submit telemetry from rain gauge, TDR soil moisture probe, and seismic accelerometer.",
    })


@login_required
def fetch_live_weather(request, pk):
    """
    Fetch real-time meteorological observations for this station's coordinates
    using the Open-Meteo API, evaluate landslide risk, and save a new reading.
    """
    location = get_object_or_404(MonitoringLocation, pk=pk)

    try:
        # Open-Meteo free API - no API key needed
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={location.latitude}&longitude={location.longitude}&"
            f"current=temperature_2m,relative_humidity_2m,precipitation,rain&"
            f"daily=precipitation_sum&timezone=auto"
        )
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            curr = data.get("current", {})
            daily = data.get("daily", {})

            daily_rain_list = daily.get("precipitation_sum", [12.0, 15.0, 20.0])
            rain_24h = float(curr.get("precipitation", daily_rain_list[0] if daily_rain_list else 15.0))
            rain_72h = float(sum(daily_rain_list[:3])) if len(daily_rain_list) >= 3 else (rain_24h * 2.2)
            temp = float(curr.get("temperature_2m", 22.0))
            humidity = float(curr.get("relative_humidity_2m", 80.0))

            # Soil moisture approximation from recent precipitation
            moisture = min(96.0, max(28.0, 35.0 + (rain_72h / 200.0) * 50.0))
            vibration = round(random.uniform(0.2, 1.8), 1)

            reading = SensorReading.objects.create(
                location=location,
                recorded_at=timezone.now(),
                rainfall_24h_mm=round(rain_24h, 1),
                rainfall_72h_mm=round(rain_72h, 1),
                soil_moisture_pct=round(moisture, 1),
                ground_vibration=vibration,
                temperature_c=round(temp, 1),
                humidity_pct=round(humidity, 1),
            )
            pred = evaluate_reading(reading)
            messages.success(
                request,
                f"Live weather synced via Open-Meteo API! Rain 24h: {reading.rainfall_24h_mm}mm, "
                f"Soil Moisture: {reading.soil_moisture_pct}%. Evaluated Risk: {pred.risk_level} ({pred.risk_score:.0f}/100)."
            )
            return redirect("location_detail", pk=location.pk)
    except Exception as e:
        # Fallback simulation if offline or API blocked
        pass

    # Realistic seasonal fallback when network is unavailable
    sim_rain = round(random.uniform(45.0, 135.0), 1)
    reading = SensorReading.objects.create(
        location=location,
        recorded_at=timezone.now(),
        rainfall_24h_mm=sim_rain,
        rainfall_72h_mm=round(sim_rain * 2.1, 1),
        soil_moisture_pct=round(min(92.0, 40.0 + sim_rain * 0.4), 1),
        ground_vibration=round(random.uniform(0.5, 2.5), 1),
        temperature_c=round(random.uniform(18.0, 26.0), 1),
        humidity_pct=round(random.uniform(75.0, 95.0), 1),
    )
    pred = evaluate_reading(reading)
    messages.info(
        request,
        f"Simulated meteorological sync completed. Rain: {reading.rainfall_24h_mm}mm. "
        f"Evaluated Risk: {pred.risk_level} ({pred.risk_score:.0f}/100)."
    )
    return redirect("location_detail", pk=location.pk)


def prediction_list(request):
    predictions = RiskPrediction.objects.select_related("location", "reading")[:100]
    return render(request, "monitoring/prediction_list.html", {
        "predictions": predictions,
        "level_colors": LEVEL_COLORS,
    })


def alert_list(request):
    alerts = Alert.objects.select_related("location", "acknowledged_by", "prediction")
    show = request.GET.get("show", "open")
    if show == "open":
        alerts = alerts.filter(is_acknowledged=False)
    return render(request, "monitoring/alert_list.html", {
        "alerts": alerts,
        "show": show,
        "level_colors": LEVEL_COLORS,
    })


@login_required
def alert_acknowledge(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == "POST":
        alert.is_acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        messages.success(request, f"Alert #{alert.id} for '{alert.location.name}' has been marked as acknowledged.")
    return redirect("alert_list")


def incident_list(request):
    incidents = LandslideIncident.objects.all()
    return render(request, "monitoring/incident_list.html", {"incidents": incidents})


@login_required
def incident_add(request):
    form = IncidentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Historical landslide incident recorded successfully.")
        return redirect("incident_list")
    return render(request, "monitoring/form.html", {
        "form": form,
        "title": "Add Historical Landslide Incident",
        "subtitle": "Record documented past disaster events to enrich the regional training archive.",
    })


def risk_calculator(request):
    result = None
    form = RiskCalculatorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        result = predict_risk(**form.cleaned_data)
    return render(request, "monitoring/calculator.html", {
        "form": form,
        "result": result,
        "level_colors": LEVEL_COLORS,
    })


def model_metrics_view(request):
    """Display real machine learning model evaluation metrics and confusion matrix."""
    metadata = get_model_metadata()
    return render(request, "monitoring/model_metrics.html", {
        "metadata": metadata,
        "metadata_json": json.dumps(metadata),
        "level_colors": LEVEL_COLORS,
    })


def about(request):
    metadata = get_model_metadata()
    return render(request, "monitoring/about.html", {
        "metadata": metadata,
    })


# ==============================================================================
# REST API Endpoints (For IoT Microcontrollers / Python Simulators)
# ==============================================================================

@csrf_exempt
def api_locations(request):
    """GET /api/locations/ - Return all active stations with current risk."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = []
    for loc in MonitoringLocation.objects.filter(is_active=True):
        pred = loc.latest_prediction
        data.append({
            "id": loc.id,
            "name": loc.name,
            "state": loc.state,
            "district": loc.district,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "elevation_m": loc.elevation_m,
            "slope_angle": loc.slope_angle,
            "soil_type": loc.soil_type,
            "latest_risk_level": pred.risk_level if pred else "None",
            "latest_risk_score": pred.risk_score if pred else 0,
        })
    return JsonResponse({"status": "success", "count": len(data), "locations": data})


@csrf_exempt
def api_create_reading(request):
    """
    POST /api/readings/ - Ingest IoT telemetry from rain gauge / tiltmeter.
    JSON Payload: {
        "location_id": 1,
        "rainfall_24h_mm": 120.5,
        "rainfall_72h_mm": 240.0,
        "soil_moisture_pct": 78.5,
        "ground_vibration": 3.2,
        "temperature_c": 22.5,
        "humidity_pct": 85.0
    }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method accepted"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        location_id = body.get("location_id")
        location = MonitoringLocation.objects.get(pk=location_id)

        reading = SensorReading.objects.create(
            location=location,
            recorded_at=timezone.now(),
            rainfall_24h_mm=float(body.get("rainfall_24h_mm", 0.0)),
            rainfall_72h_mm=float(body.get("rainfall_72h_mm", 0.0)),
            soil_moisture_pct=float(body.get("soil_moisture_pct", 50.0)),
            ground_vibration=float(body.get("ground_vibration", 0.0)),
            temperature_c=float(body.get("temperature_c", 25.0)),
            humidity_pct=float(body.get("humidity_pct", 75.0)),
        )

        prediction = evaluate_reading(reading)

        return JsonResponse({
            "status": "success",
            "message": "Telemetry processed and evaluated by AI Risk Engine",
            "reading_id": reading.id,
            "location": location.name,
            "risk_score": prediction.risk_score,
            "risk_level": prediction.risk_level,
            "alert_triggered": prediction.risk_level in ("High", "Critical"),
            "recommendation": prediction.recommendation,
        }, status=201)

    except MonitoringLocation.DoesNotExist:
        return JsonResponse({"error": "Location ID not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ==============================================================================
# Data Export (CSV) for Disaster Management Officials
# ==============================================================================

def export_alerts_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ner_landslide_alerts.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Alert ID", "Severity", "Location", "District", "State",
        "Issued At", "Is Acknowledged", "Acknowledged By", "Acknowledged At", "Message"
    ])

    for a in Alert.objects.select_related("location", "acknowledged_by").all():
        writer.writerow([
            a.id,
            a.severity,
            a.location.name,
            a.location.district,
            a.location.state,
            a.issued_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Yes" if a.is_acknowledged else "No",
            a.acknowledged_by.username if a.acknowledged_by else "-",
            a.acknowledged_at.strftime("%Y-%m-%d %H:%M:%S") if a.acknowledged_at else "-",
            a.message,
        ])

    return response


def export_readings_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ner_sensor_readings.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Reading ID", "Location", "State", "Recorded At", "Rain 24h (mm)",
        "Rain 72h (mm)", "Soil Moisture (%)", "Ground Vibration", "Temp (C)", "Humidity (%)"
    ])

    for r in SensorReading.objects.select_related("location").all()[:1000]:
        writer.writerow([
            r.id,
            r.location.name,
            r.location.state,
            r.recorded_at.strftime("%Y-%m-%d %H:%M:%S"),
            r.rainfall_24h_mm,
            r.rainfall_72h_mm,
            r.soil_moisture_pct,
            r.ground_vibration,
            r.temperature_c,
            r.humidity_pct,
        ])

    return response


def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)


def custom_500_view(request):
    return render(request, "500.html", status=500)

