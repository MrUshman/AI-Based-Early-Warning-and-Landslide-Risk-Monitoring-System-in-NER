"""Seed demo data: NER monitoring locations, readings, predictions,
alerts (auto-generated), historical incidents and a demo admin user.

Run:  python manage.py seed_data
Safe to re-run: it clears previous demo monitoring data first.
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import LandslideIncident, MonitoringLocation, SensorReading
from monitoring.risk_engine import evaluate_reading

# name, state, district, lat, lon, elevation, slope, soil,
# latest (rain24, rain72, soil_moisture, vibration)
LOCATIONS = [
    ("NH-10 Highway, km 32", "Sikkim", "Gangtok", 27.25, 88.50, 1250, 42, "clay", (145, 290, 82, 3.5)),
    ("Gangtok Town Slope", "Sikkim", "Gangtok", 27.33, 88.61, 1650, 35, "loamy", (90, 210, 68, 1.5)),
    ("Sonapur Tunnel Area, NH-6", "Meghalaya", "East Jaintia Hills", 25.18, 92.40, 900, 46, "silt", (160, 320, 86, 2.0)),
    ("Shillong - Dawki Road", "Meghalaya", "East Khasi Hills", 25.45, 91.85, 1400, 33, "loamy", (70, 160, 60, 1.0)),
    ("Aizawl - Hunthar Veng", "Mizoram", "Aizawl", 23.72, 92.72, 1100, 44, "clay", (120, 260, 78, 2.5)),
    ("Kohima - NH-29 Slide Zone", "Nagaland", "Kohima", 25.62, 94.08, 1420, 39, "rocky", (85, 190, 63, 4.0)),
    ("Itanagar - NH-415", "Arunachal Pradesh", "Papum Pare", 27.08, 93.60, 750, 41, "silt", (110, 240, 74, 1.8)),
    ("Bomdila Pass Road", "Arunachal Pradesh", "West Kameng", 27.26, 92.42, 2420, 48, "rocky", (55, 130, 52, 3.0)),
    ("Ukhrul Road Slope", "Manipur", "Ukhrul", 25.10, 94.36, 1660, 37, "clay", (65, 150, 58, 5.5)),
    ("Guwahati - Fancy Bazar Hill", "Assam", "Kamrup Metropolitan", 26.18, 91.74, 320, 28, "loamy", (45, 100, 48, 0.8)),
    ("Haflong - New Haflong", "Assam", "Dima Hasao", 25.16, 93.02, 680, 40, "silt", (130, 270, 80, 2.2)),
    ("Agartala - Assam Rifles Slope", "Tripura", "West Tripura", 23.86, 91.30, 180, 24, "loamy", (35, 85, 42, 0.5)),
]

INCIDENTS = [
    ("Malpa area road stretch", "Arunachal Pradesh", "West Kameng", "2023-07-11",
     "Monsoon slide blocked the highway for two days.", 210, "Road blocked, emergency clearance deployed by Border Roads Organisation (BRO)."),
    ("Sonapur, NH-6", "Meghalaya", "East Jaintia Hills", "2024-06-18",
     "Mudslide after continuous heavy rain buried part of the road.", 280, "Vehicles stranded, traffic restored in 36 hours by NHIDCL emergency crews."),
    ("Hunthar Veng", "Mizoram", "Aizawl", "2024-05-28",
     "Slope failure during cyclone remnant rainfall damaged houses below the road.", 190, "Structures damaged, 42 families evacuated to disaster relief shelters."),
    ("NH-10 near Rangpo", "Sikkim", "Pakyong", "2023-10-05",
     "Slide following heavy rain and a swollen river cut off the highway.", 240, "Highway link breached at multiple sections; NDRF and SDRF mobilized."),
    ("New Haflong", "Assam", "Dima Hasao", "2022-05-16",
     "Massive slides and flooding devastated the railway station area during extreme rain.", 320, "Railway and road infrastructure severely damaged; multi-agency restoration."),
]


class Command(BaseCommand):
    help = "Seed the database with NER demo data"

    def handle(self, *args, **options):
        SensorReading.objects.all().delete()
        MonitoringLocation.objects.all().delete()
        LandslideIncident.objects.all().delete()

        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write("Demo superuser created: admin / admin123")

        rng = random.Random(42)
        now = timezone.now()
        for (name, state, district, lat, lon, elev, slope, soil, latest) in LOCATIONS:
            loc = MonitoringLocation.objects.create(
                name=name, state=state, district=district, latitude=lat, longitude=lon,
                elevation_m=elev, slope_angle=slope, soil_type=soil,
            )
            # 5 older readings trending towards the latest values
            for i in range(5, 0, -1):
                factor = 1 - i * 0.12
                reading = SensorReading.objects.create(
                    location=loc, recorded_at=now - timedelta(hours=i * 12),
                    rainfall_24h_mm=round(latest[0] * factor * rng.uniform(0.8, 1.05), 1),
                    rainfall_72h_mm=round(latest[1] * factor * rng.uniform(0.85, 1.05), 1),
                    soil_moisture_pct=round(min(95, latest[2] * factor * rng.uniform(0.9, 1.05)), 1),
                    ground_vibration=round(max(0, latest[3] + rng.uniform(-0.6, 0.6)), 1),
                    temperature_c=rng.randint(16, 29), humidity_pct=rng.randint(65, 95),
                )
                evaluate_reading(reading)
            # Latest reading
            reading = SensorReading.objects.create(
                location=loc, recorded_at=now,
                rainfall_24h_mm=latest[0], rainfall_72h_mm=latest[1],
                soil_moisture_pct=latest[2], ground_vibration=latest[3],
                temperature_c=24, humidity_pct=88,
            )
            evaluate_reading(reading)

        for name, state, district, date_str, desc, rain, damage in INCIDENTS:
            LandslideIncident.objects.create(
                location_name=name, state=state, district=district,
                occurred_on=date_str, description=desc,
                rainfall_before_mm=rain, damage_summary=damage,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(LOCATIONS)} locations with readings, predictions, alerts and {len(INCIDENTS)} incidents."
        ))
