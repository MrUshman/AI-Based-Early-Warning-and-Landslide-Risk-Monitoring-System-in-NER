import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Avg

from .models import (
    MonitoringLocation, SensorReading, RiskPrediction, Alert, LandslideIncident, NER_STATES
)
from .forms import ReadingForm, IncidentForm, AlertActionForm
from .risk import evaluate_risk


def is_ddma_or_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name='DDMA_Officer').exists()
    )


def is_operator_or_above(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=['Field_Operator', 'DDMA_Officer']).exists()
    )


# 1. Public Dashboard
def public_dashboard(request):
    """
    Public landing dashboard.
    Summarizes current regional threat levels, active alerts, map coordinates,
    and priority high-risk slopes across the 8 NER states.
    """
    locations = MonitoringLocation.objects.filter(is_active=True).prefetch_related('predictions', 'alerts')

    # Calculate status counts across all locations
    critical_locs = []
    high_locs = []
    moderate_locs = []
    low_locs = []

    for loc in locations:
        level = loc.current_risk_level
        if level == 'CRITICAL':
            critical_locs.append(loc)
        elif level == 'HIGH':
            high_locs.append(loc)
        elif level == 'MODERATE':
            moderate_locs.append(loc)
        else:
            low_locs.append(loc)

    # Active alerts
    active_alerts = Alert.objects.filter(
        status__in=['ACTIVE', 'ACKNOWLEDGED']
    ).select_related('location', 'prediction').order_by('-created_at')[:6]

    # Locations sorted by risk score descending
    sorted_locations = sorted(
        locations,
        key=lambda l: (l.current_risk_score, l.name),
        reverse=True
    )

    context = {
        'total_locations_count': locations.count(),
        'critical_count': len(critical_locs),
        'high_count': len(high_locs),
        'moderate_count': len(moderate_locs),
        'low_count': len(low_locs),
        'active_alerts': active_alerts,
        'top_risk_locations': sorted_locations[:6],
        'all_locations': sorted_locations,
        'states': [s[0] for s in NER_STATES],
    }
    return render(request, 'monitoring/dashboard.html', context)


# 2. Locations List & Filter
def locations_list(request):
    """
    Displays all 12 monitoring locations with state and risk level filters.
    """
    state_filter = request.GET.get('state', '').strip()
    risk_filter = request.GET.get('risk', '').strip().upper()
    search_query = request.GET.get('q', '').strip()

    locations = MonitoringLocation.objects.filter(is_active=True).prefetch_related('predictions')

    if state_filter:
        locations = locations.filter(state__iexact=state_filter)

    if search_query:
        locations = locations.filter(
            Q(name__icontains=search_query) |
            Q(district__icontains=search_query) |
            Q(nearest_town_or_road__icontains=search_query)
        )

    # Filter in Python by risk level if specified
    filtered_list = []
    for loc in locations:
        if risk_filter and loc.current_risk_level != risk_filter:
            continue
        filtered_list.append(loc)

    # Sort by current risk score descending
    filtered_list.sort(key=lambda l: l.current_risk_score, reverse=True)

    context = {
        'locations': filtered_list,
        'selected_state': state_filter,
        'selected_risk': risk_filter,
        'search_query': search_query,
        'states': [s[0] for s in NER_STATES],
    }
    return render(request, 'monitoring/locations_list.html', context)


# 3. Location Detail View
def location_detail(request, pk):
    """
    Detailed slope dossier: current risk score, explainable breakdown bars,
    Chart.js trend data, sensor history, active alerts, and past incidents.
    """
    location = get_object_or_404(MonitoringLocation, pk=pk)
    recent_readings = location.readings.select_related('prediction', 'recorded_by').order_by('-recorded_at')[:10]
    alerts = location.alerts.select_related('prediction').order_by('-created_at')[:5]
    incidents = location.incidents.order_by('-occurred_at')[:5]

    latest_pred = location.latest_prediction
    latest_reading = location.latest_reading

    context = {
        'location': location,
        'latest_pred': latest_pred,
        'latest_reading': latest_reading,
        'recent_readings': recent_readings,
        'alerts': alerts,
        'incidents': incidents,
    }
    return render(request, 'monitoring/location_detail.html', context)


# 4. Active Alerts Board
def alerts_list(request):
    """
    Public alert advisory board showing all active High and Critical alerts.
    """
    state_filter = request.GET.get('state', '').strip()
    level_filter = request.GET.get('level', '').strip().upper()
    status_filter = request.GET.get('status', 'ACTIVE_ALL')

    alerts_qs = Alert.objects.select_related('location', 'prediction', 'acknowledged_by')

    if status_filter == 'ACTIVE_ALL':
        alerts_qs = alerts_qs.filter(status__in=['ACTIVE', 'ACKNOWLEDGED'])
    elif status_filter in ['ACTIVE', 'ACKNOWLEDGED', 'CLOSED']:
        alerts_qs = alerts_qs.filter(status=status_filter)

    if state_filter:
        alerts_qs = alerts_qs.filter(location__state__iexact=state_filter)

    if level_filter in ['HIGH', 'CRITICAL']:
        alerts_qs = alerts_qs.filter(level=level_filter)

    context = {
        'alerts': alerts_qs.order_by('-created_at'),
        'selected_state': state_filter,
        'selected_level': level_filter,
        'selected_status': status_filter,
        'states': [s[0] for s in NER_STATES],
    }
    return render(request, 'monitoring/alerts_list.html', context)


# 5. Alert Detail & Operational Action
def alert_detail(request, pk):
    """
    Detailed alert dossier with action history and DDMA response controls.
    """
    alert = get_object_or_404(Alert.objects.select_related('location', 'prediction', 'acknowledged_by', 'closed_by'), pk=pk)
    action_form = AlertActionForm()

    context = {
        'alert': alert,
        'action_form': action_form,
        'can_manage': is_ddma_or_admin_user(request.user),
    }
    return render(request, 'monitoring/alert_detail.html', context)


# 6. Alert Acknowledge (DDMA / Admin only)
@login_required
def alert_acknowledge(request, pk):
    """
    Allows a DDMA officer to acknowledge receipt of an alert and log immediate ground actions.
    """
    if not is_ddma_or_admin_user(request.user):
        return HttpResponseForbidden("Permission Denied: Only DDMA Officers or Administrators can acknowledge alerts.")

    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        form = AlertActionForm(request.POST)
        if form.is_valid():
            note = form.cleaned_data['action_note']
            alert.status = 'ACKNOWLEDGED'
            alert.acknowledged_by = request.user
            alert.acknowledged_at = timezone.now()
            existing_note = alert.action_taken_note or ""
            alert.action_taken_note = f"{existing_note}\n[ACKNOWLEDGED by {request.user.get_full_name() or request.user.username} at {timezone.now().strftime('%d %b %Y, %I:%M %p IST')}]: {note}".strip()
            alert.save()
            messages.success(request, f"Alert for {alert.location.name} successfully acknowledged.")
            return redirect('alert_detail', pk=alert.pk)

    return redirect('alert_detail', pk=alert.pk)


# 7. Alert Close (DDMA / Admin only)
@login_required
def alert_close(request, pk):
    """
    Allows a DDMA officer to close an alert once slope conditions stabilize or road is cleared.
    """
    if not is_ddma_or_admin_user(request.user):
        return HttpResponseForbidden("Permission Denied: Only DDMA Officers or Administrators can close alerts.")

    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        form = AlertActionForm(request.POST)
        if form.is_valid():
            note = form.cleaned_data['action_note']
            alert.status = 'CLOSED'
            alert.closed_by = request.user
            alert.closed_at = timezone.now()
            existing_note = alert.action_taken_note or ""
            alert.action_taken_note = f"{existing_note}\n[CLOSED by {request.user.get_full_name() or request.user.username} at {timezone.now().strftime('%d %b %Y, %I:%M %p IST')}]: {note}".strip()
            alert.save()
            messages.success(request, f"Alert for {alert.location.name} has been closed and archived in history.")
            return redirect('alert_detail', pk=alert.pk)

    return redirect('alert_detail', pk=alert.pk)


# 8. Add Sensor Reading (Operator & above)
@login_required
def reading_add(request):
    """
    Enters a new reading, evaluates the explainable risk engine,
    saves the prediction, and auto-triggers an alert if HIGH or CRITICAL.
    """
    if not is_operator_or_above(request.user):
        messages.error(request, "Permission Denied: Only Field Operators or Officers can add readings.")
        return redirect('public_dashboard')

    initial_loc_id = request.GET.get('location')

    if request.method == 'POST':
        form = ReadingForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.recorded_by = request.user
            reading.save()

            location = reading.location

            # Evaluate with Explainable Risk Engine
            risk_result = evaluate_risk(
                rainfall_24h_mm=reading.rainfall_24h_mm,
                rainfall_72h_mm=reading.rainfall_72h_mm,
                soil_moisture_percent=reading.soil_moisture_percent,
                slope_angle=location.slope_angle,
                ground_vibration=reading.ground_vibration,
                location_name=location.name
            )

            prediction = RiskPrediction.objects.create(
                location=location,
                reading=reading,
                rainfall_score=risk_result['rainfall_score'],
                soil_score=risk_result['soil_score'],
                slope_score=risk_result['slope_score'],
                vibration_score=risk_result['vibration_score'],
                total_score=risk_result['total_score'],
                risk_level=risk_result['risk_level'],
                recommendation=risk_result['recommendation'],
                predicted_at=reading.recorded_at
            )

            # Auto-alert rule: create alert for HIGH and CRITICAL
            if risk_result['should_alert']:
                Alert.objects.create(
                    location=location,
                    prediction=prediction,
                    title=f"{risk_result['risk_level']} Landslide Threat: {location.name}",
                    message=risk_result['recommendation'],
                    level=risk_result['risk_level'],
                    status='ACTIVE',
                    created_at=reading.recorded_at
                )
                messages.warning(
                    request,
                    f"CRITICAL WARNING: Reading triggered a {risk_result['risk_level']} alert (Score: {risk_result['total_score']}/100)!"
                )
            else:
                messages.success(
                    request,
                    f"Reading saved. Evaluated risk level is {risk_result['risk_level']} (Score: {risk_result['total_score']}/100)."
                )

            return redirect('location_detail', pk=location.pk)
    else:
        initial_data = {}
        if initial_loc_id:
            initial_data['location'] = initial_loc_id
        form = ReadingForm(initial=initial_data)

    locations = MonitoringLocation.objects.filter(is_active=True).values('id', 'name', 'state', 'slope_angle')
    locations_json = json.dumps(list(locations))

    context = {
        'form': form,
        'locations_json': locations_json,
    }
    return render(request, 'monitoring/reading_form.html', context)


# 9. Predictions History List
@login_required
def predictions_list(request):
    """
    Score history with factor breakdowns.
    """
    preds = RiskPrediction.objects.select_related('location', 'reading', 'reading__recorded_by').order_by('-predicted_at')[:50]
    return render(request, 'monitoring/predictions_list.html', {'predictions': preds})


# 10. Incidents List & Add
def incidents_list(request):
    """
    Public log of verified ground landslide incidents.
    """
    incidents = LandslideIncident.objects.select_related('location', 'reported_by').order_by('-occurred_at')
    return render(request, 'monitoring/incidents_list.html', {'incidents': incidents})


@login_required
def incident_add(request):
    """
    Record an actual landslide incident with road blockage status.
    """
    if not is_operator_or_above(request.user):
        messages.error(request, "Permission Denied: Only authorized personnel can report incidents.")
        return redirect('incidents_list')

    if request.method == 'POST':
        form = IncidentForm(request.POST)
        if form.is_valid():
            inc = form.save(commit=False)
            inc.reported_by = request.user
            inc.save()
            messages.success(request, f"Incident at {inc.location.name} recorded into official database.")
            return redirect('incidents_list')
    else:
        form = IncidentForm()

    return render(request, 'monitoring/incident_form.html', {'form': form})


# 11. Safety Guidance
def safety_guidance(request):
    """
    Public emergency guidelines: before travelling, warning signs,
    response if a slide occurs, and emergency 112 dialing instructions.
    """
    return render(request, 'monitoring/safety.html')


# 12. About & Agencies Workflow
def about_agencies(request):
    """
    Explains the NER landslide risk architecture and maps real-world agency responsibilities
    (IMD, GSI, NDMA, DDMA, NDRF, BRO/NHIDCL).
    """
    return render(request, 'monitoring/about.html')


# 13. Officer Dashboard / Queue
@login_required
def officer_dashboard(request):
    """
    Operational command center for logged-in officers:
    - Unacknowledged active alerts
    - Locations with stale sensor readings (> 12 hours)
    - Quick reading submission & incident reporting
    """
    unack_alerts = Alert.objects.filter(status='ACTIVE').select_related('location', 'prediction').order_by('-created_at')
    ack_alerts = Alert.objects.filter(status='ACKNOWLEDGED').select_related('location', 'prediction').order_by('-created_at')

    # Find stale locations (no reading in last 12 hours)
    twelve_hours_ago = timezone.now() - timezone.timedelta(hours=12)
    all_locs = MonitoringLocation.objects.filter(is_active=True).prefetch_related('readings', 'predictions')

    stale_locations = []
    active_locations = []

    for loc in all_locs:
        last_r = loc.latest_reading
        if not last_r or last_r.recorded_at < twelve_hours_ago:
            stale_locations.append({'location': loc, 'last_reading': last_r})
        else:
            active_locations.append({'location': loc, 'last_reading': last_r})

    context = {
        'unacknowledged_alerts': unack_alerts,
        'acknowledged_alerts': ack_alerts,
        'stale_locations': stale_locations,
        'active_locations': active_locations,
        'user_is_ddma': is_ddma_or_admin_user(request.user),
    }
    return render(request, 'monitoring/officer_dashboard.html', context)


# --- JSON APIs for Maps and Charts ---

def api_locations_geojson(request):
    """
    Returns GeoJSON-compatible data for all 12 monitoring locations
    for Leaflet.js interactive GIS map.
    """
    locations = MonitoringLocation.objects.filter(is_active=True).prefetch_related('predictions')
    features = []

    for loc in locations:
        features.append({
            'id': loc.id,
            'name': loc.name,
            'state': loc.state,
            'district': loc.district,
            'nearest_town_or_road': loc.nearest_town_or_road,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'slope_angle': loc.slope_angle,
            'soil_type': loc.soil_type,
            'risk_level': loc.current_risk_level,
            'risk_score': loc.current_risk_score,
            'color': loc.risk_color_hex,
            'icon': loc.risk_icon,
            'detail_url': f"/locations/{loc.id}/",
        })

    return JsonResponse({'locations': features})


def api_location_trend(request, pk):
    """
    Returns time-series risk score and rainfall for Chart.js on location detail page.
    """
    location = get_object_or_404(MonitoringLocation, pk=pk)
    predictions = location.predictions.select_related('reading').order_by('predicted_at')[:15]

    labels = []
    scores = []
    rain_scores = []
    soil_scores = []

    for p in predictions:
        labels.append(p.predicted_at.strftime('%d %b, %H:%M'))
        scores.append(p.total_score)
        rain_scores.append(p.rainfall_score)
        soil_scores.append(p.soil_score)

    return JsonResponse({
        'location_name': location.name,
        'labels': labels,
        'scores': scores,
        'rainfall_scores': rain_scores,
        'soil_scores': soil_scores,
    })


def api_calculate_preview(request):
    """
    AJAX endpoint allowing live risk calculation as officer types in the Add Reading form.
    """
    try:
        r24 = float(request.GET.get('r24', 0))
        r72 = float(request.GET.get('r72', 0))
        sm = float(request.GET.get('sm', 0))
        slope = float(request.GET.get('slope', 0))
        vib = float(request.GET.get('vib', 0))
        loc_name = request.GET.get('name', 'Preview Slope')

        res = evaluate_risk(r24, r72, sm, slope, vib, loc_name)
        return JsonResponse({'success': True, 'data': res})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
