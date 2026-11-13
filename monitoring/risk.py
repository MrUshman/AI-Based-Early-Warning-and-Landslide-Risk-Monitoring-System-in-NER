"""
Explainable AI Risk Engine for Landslide Early Warning System (NER).
Transparent weighted scoring model:
Total Score (0-100) = Rainfall (40) + Soil Moisture (25) + Slope Angle (20) + Ground Vibration (15)

Thresholds:
- 0 to 24: LOW (Normal monitoring continues)
- 25 to 49: MODERATE (Watch closely; increase reading frequency)
- 50 to 74: HIGH (Alert auto-created. Officer review, public warning, traffic control)
- 75 to 100: CRITICAL (Alert auto-created. Immediate action: road closure & evacuation readiness)
"""

from typing import Dict, Any, Tuple


def calculate_rainfall_score(rainfall_24h_mm: float, rainfall_72h_mm: float) -> float:
    """
    Rainfall factor (Max 40 points).
    Combines intense 24h event (max 24 pts) with 72h antecedent saturation rain (max 16 pts).
    - 24h max benchmark: 150mm (intense cloudburst/torrential rain)
    - 72h max benchmark: 300mm (sustained multi-day monsoon rain)
    """
    r24 = max(0.0, float(rainfall_24h_mm))
    r72 = max(0.0, float(rainfall_72h_mm))

    score_24h = min(24.0, (r24 / 150.0) * 24.0)
    score_72h = min(16.0, (r72 / 300.0) * 16.0)

    total_rain = score_24h + score_72h
    return round(min(40.0, total_rain), 1)


def calculate_soil_moisture_score(soil_moisture_percent: float) -> float:
    """
    Soil Moisture factor (Max 25 points).
    Saturated slope soil loses shear strength and liquefies under load.
    Scale: 0% to 100% moisture.
    """
    sm = max(0.0, min(100.0, float(soil_moisture_percent)))
    score = (sm / 100.0) * 25.0
    return round(score, 1)


def calculate_slope_score(slope_angle_degrees: float) -> float:
    """
    Slope Angle factor (Max 20 points).
    Slopes > 45° are high risk; 50°+ represents cut slopes and steep ravines.
    Scale: 0° to 50° mapped to 0 to 20 points.
    """
    slope = max(0.0, float(slope_angle_degrees))
    # Cap at 50 degrees for maximum risk factor
    score = min(20.0, (slope / 50.0) * 20.0)
    return round(score, 1)


def calculate_vibration_score(ground_vibration_mms: float) -> float:
    """
    Ground Vibration factor (Max 15 points).
    Measures micro-tremors, blasting, heavy vehicle resonance or creeping shear planes.
    Standard scale: 0.0 to 10.0 mm/s peak particle velocity.
    """
    vib = max(0.0, float(ground_vibration_mms))
    score = min(15.0, (vib / 10.0) * 15.0)
    return round(score, 1)


def determine_risk_level(total_score: float) -> str:
    """
    Classify total score into 4 standard levels.
    """
    score = round(total_score, 1)
    if score < 25.0:
        return 'LOW'
    elif score < 50.0:
        return 'MODERATE'
    elif score < 75.0:
        return 'HIGH'
    else:
        return 'CRITICAL'


def generate_recommendation(
    location_name: str,
    total_score: float,
    risk_level: str,
    rainfall_score: float,
    soil_score: float,
    slope_score: float,
    vibration_score: float
) -> str:
    """
    Produces actionable plain-language recommendation for field teams & public safety.
    """
    triggers = []
    if rainfall_score >= 28.0:
        triggers.append("extreme monsoon rainfall accumulation")
    elif rainfall_score >= 20.0:
        triggers.append("heavy recent rainfall")

    if soil_score >= 20.0:
        triggers.append("near-complete soil saturation (high pore water pressure)")
    elif soil_score >= 15.0:
        triggers.append("high soil moisture")

    if slope_score >= 16.0:
        triggers.append("steep unstable cut-slope geometry")

    if vibration_score >= 8.0:
        triggers.append("abnormal ground vibration / slope creep detected")

    trigger_phrase = f" driven by {', '.join(triggers)}" if triggers else ""

    if risk_level == 'CRITICAL':
        return (
            f"CRITICAL RISK ({total_score:.1f}/100) at {location_name}{trigger_phrase}. "
            f"Immediate action required: Impose immediate vehicular traffic restriction with BRO/NHIDCL and local police. "
            f"Notify District Disaster Management Authority (DDMA), activate SDRF/NDRF standby units, "
            f"and initiate evacuation protocol for vulnerable settlements within 500m of the slope."
        )
    elif risk_level == 'HIGH':
        return (
            f"HIGH RISK ({total_score:.1f}/100) at {location_name}{trigger_phrase}. "
            f"Action required: Issue public travel advisory on this highway sector. "
            f"Deploy quick-response observation teams, verify drainage channels for debris clogs, "
            f"and prepare heavy machinery (JCB/excavators) at nearby staging depots for rapid clearance."
        )
    elif risk_level == 'MODERATE':
        return (
            f"MODERATE RISK ({total_score:.1f}/100) at {location_name}{trigger_phrase}. "
            f"Advisory: Slope stability is deteriorating. Field officers should increase sensor reading frequency "
            f"to every 4-6 hours. Monitor road drainage and watch for tension cracks or sudden muddy seepage."
        )
    else:
        return (
            f"LOW RISK ({total_score:.1f}/100) at {location_name}. "
            f"Conditions normal. Continue routine daily monitoring according to standard monsoon SOPs."
        )


def evaluate_risk(
    rainfall_24h_mm: float,
    rainfall_72h_mm: float,
    soil_moisture_percent: float,
    slope_angle: float,
    ground_vibration: float,
    location_name: str = "Monitored Location"
) -> Dict[str, Any]:
    """
    Pure explainable risk evaluation function.
    Given raw field readings, returns complete transparent breakdown, total score, level,
    recommendation, and boolean flag indicating if an alert is warranted.
    """
    rain_pts = calculate_rainfall_score(rainfall_24h_mm, rainfall_72h_mm)
    soil_pts = calculate_soil_moisture_score(soil_moisture_percent)
    slope_pts = calculate_slope_score(slope_angle)
    vib_pts = calculate_vibration_score(ground_vibration)

    total = round(rain_pts + soil_pts + slope_pts + vib_pts, 1)
    # Ensure total is capped at 100.0
    total = min(100.0, total)
    level = determine_risk_level(total)
    rec = generate_recommendation(location_name, total, level, rain_pts, soil_pts, slope_pts, vib_pts)

    return {
        'rainfall_score': rain_pts,
        'soil_score': soil_pts,
        'slope_score': slope_pts,
        'vibration_score': vib_pts,
        'total_score': total,
        'risk_level': level,
        'should_alert': level in ['HIGH', 'CRITICAL'],
        'recommendation': rec,
        'breakdown_percent': {
            'rainfall': round((rain_pts / 40.0) * 100, 1),
            'soil': round((soil_pts / 25.0) * 100, 1),
            'slope': round((slope_pts / 20.0) * 100, 1),
            'vibration': round((vib_pts / 15.0) * 100, 1),
        }
    }
