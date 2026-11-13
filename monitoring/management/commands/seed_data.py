import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.utils import timezone
from monitoring.models import (
    MonitoringLocation, SensorReading, RiskPrediction, Alert, LandslideIncident
)
from monitoring.risk import evaluate_risk


class Command(BaseCommand):
    help = "Seed database with 12 NER monitoring locations, users, sensor readings, alerts, and incidents"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing seed process for Landslide EWS (NER)..."))

        # 1. Setup Groups & Roles
        ddma_group, _ = Group.objects.get_or_create(name='DDMA_Officer')
        operator_group, _ = Group.objects.get_or_create(name='Field_Operator')

        # 2. Setup Standard Demo Users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@disastermanagement.gov.in', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.first_name = 'NER State'
            admin_user.last_name = 'Administrator'
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Super Admin: admin / Admin@123"))

        ddma_user, created = User.objects.get_or_create(
            username='ddma_officer',
            defaults={'email': 'ddma.officer@ner-disaster.gov.in', 'is_staff': True}
        )
        if created:
            ddma_user.set_password('Officer@123')
            ddma_user.first_name = 'Tsering'
            ddma_user.last_name = 'Dorjee (DDMA)'
            ddma_user.save()
            ddma_user.groups.add(ddma_group)
            self.stdout.write(self.style.SUCCESS("Created DDMA Officer: ddma_officer / Officer@123"))

        operator_user, created = User.objects.get_or_create(
            username='field_operator',
            defaults={'email': 'operator@ner-monitoring.gov.in', 'is_staff': False}
        )
        if created:
            operator_user.set_password('Operator@123')
            operator_user.first_name = 'Rahul'
            operator_user.last_name = 'Sharma (Field)'
            operator_user.save()
            operator_user.groups.add(operator_group)
            self.stdout.write(self.style.SUCCESS("Created Field Operator: field_operator / Operator@123"))

        # 3. Seed 12 Locations
        locations_data = [
            {
                "name": "Sonapur Tunnel Area, NH-6",
                "state": "Meghalaya",
                "district": "East Jaintia Hills",
                "nearest_town_or_road": "NH-6 / Sonapur Bridge",
                "latitude": 25.1092,
                "longitude": 92.3614,
                "slope_angle": 45.0,
                "soil_type": "Alternating Sandstone & Friable Shale",
                "description": "Crucial highway bottleneck linking Barak Valley (Assam), Mizoram, and Tripura. High vulnerability to torrential monsoon mudslides and slope failures.",
            },
            {
                "name": "NH-10 km 32",
                "state": "Sikkim",
                "district": "Pakyong / Kalimpong border",
                "nearest_town_or_road": "NH-10 Teesta Corridor",
                "latitude": 27.2038,
                "longitude": 88.5132,
                "slope_angle": 42.0,
                "soil_type": "Weathered Phyllite & Schist colluvium",
                "description": "Strategic lifeline connecting Gangtok with Siliguri. Subject to aggressive toe cutting by river Teesta during high-volume discharge.",
            },
            {
                "name": "Gangtok Town Slope",
                "state": "Sikkim",
                "district": "East Sikkim",
                "nearest_town_or_road": "Deorali / Development Area",
                "latitude": 27.3389,
                "longitude": 88.6065,
                "slope_angle": 36.0,
                "soil_type": "Mica Schist with heavy clay overburden",
                "description": "Steep urban slope directly situated above residential settlements and bazaar infrastructure in the state capital.",
            },
            {
                "name": "Shillong-Dawki Road",
                "state": "Meghalaya",
                "district": "East Khasi Hills",
                "nearest_town_or_road": "Pynursla Gorge Stretch",
                "latitude": 25.3854,
                "longitude": 91.8842,
                "slope_angle": 38.0,
                "soil_type": "Quartzite & Ferruginous Sandstone",
                "description": "Scenic hill highway carrying dense international tourist traffic and commercial transit to the Bangladesh border.",
            },
            {
                "name": "Aizawl-Hunthar Veng",
                "state": "Mizoram",
                "district": "Aizawl",
                "nearest_town_or_road": "Hunthar Veng Western Bypass",
                "latitude": 23.7428,
                "longitude": 92.7176,
                "slope_angle": 39.0,
                "soil_type": "Siltstone, Mudstone & Saturated Colluvium",
                "description": "Historic active subsidence and creeping slope zone. Threatens the only arterial western access highway into Aizawl.",
            },
            {
                "name": "Kohima NH-29",
                "state": "Nagaland",
                "district": "Kohima",
                "nearest_town_or_road": "Old KMC Checkpost, NH-29",
                "latitude": 25.6701,
                "longitude": 94.1077,
                "slope_angle": 41.0,
                "soil_type": "Disintegrated Clayey Shale (Barail Group)",
                "description": "The primary overland artery sustaining goods transit into Kohima and Manipur. High seasonal sliding risk.",
            },
            {
                "name": "Itanagar NH-415",
                "state": "Arunachal Pradesh",
                "district": "Papum Pare",
                "nearest_town_or_road": "Chandranagar - Gohpur stretch",
                "latitude": 27.0979,
                "longitude": 93.6166,
                "slope_angle": 35.0,
                "soil_type": "Soft Tertiary Sandstone & River Silt",
                "description": "Main four-lane expressway corridor approaching the capital. Vulnerable to flash runoff embankment breaches.",
            },
            {
                "name": "Bomdila Pass Road",
                "state": "Arunachal Pradesh",
                "district": "West Kameng",
                "nearest_town_or_road": "Bhalukpong-Bomdila-Tawang Highway",
                "latitude": 27.2645,
                "longitude": 92.4227,
                "slope_angle": 44.0,
                "soil_type": "Granitic Gneiss & Fragmented Talus",
                "description": "High-altitude strategic defense highway sector at 8,500 ft. Prone to rockfalls and intense freeze-thaw slip planes.",
            },
            {
                "name": "Ukhrul Road Slope",
                "state": "Manipur",
                "district": "Ukhrul",
                "nearest_town_or_road": "Imphal-Ukhrul Hill Road",
                "latitude": 25.1161,
                "longitude": 94.3622,
                "slope_angle": 37.0,
                "soil_type": "Disang Flysch, Black Shale & Clay",
                "description": "Lifeline connecting district headquarters to Imphal valley. Notorious for expansive clay swelling and mudslides.",
            },
            {
                "name": "Guwahati-Fancy Bazar Hill",
                "state": "Assam",
                "district": "Kamrup Metropolitan",
                "nearest_town_or_road": "Brahmaputra South Hillock",
                "latitude": 26.1852,
                "longitude": 91.7458,
                "slope_angle": 32.0,
                "soil_type": "Weathered Precambrian Granitic Residual Soil",
                "description": "Dense urban slope with heavy toe excavations, posing direct hazards to adjacent marketplace communities.",
            },
            {
                "name": "Haflong-New Haflong",
                "state": "Assam",
                "district": "Dima Hasao",
                "nearest_town_or_road": "Lumding-Badarpur Highway & Rail Link",
                "latitude": 25.1764,
                "longitude": 93.0238,
                "slope_angle": 43.0,
                "soil_type": "Jaintia Group Crushed Sandstone & Silt",
                "description": "Severe geotechnical instability zone; experienced massive regional debris washouts in recent monsoons.",
            },
            {
                "name": "Agartala-Assam Rifles Slope",
                "state": "Tripura",
                "district": "West Tripura",
                "nearest_town_or_road": "Kunjaban Ridge Road",
                "latitude": 23.8438,
                "longitude": 91.2868,
                "slope_angle": 30.0,
                "soil_type": "Tipam Sandstone with Red Ferruginous Clay",
                "description": "Elevated ridge slope inside the capital precinct prone to gully erosions and sudden embankment slips during cloudbursts.",
            },
        ]

        created_locations = {}
        for loc_data in locations_data:
            loc, _ = MonitoringLocation.objects.update_or_create(
                name=loc_data["name"],
                defaults=loc_data
            )
            created_locations[loc.name] = loc

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_locations)} Monitoring Locations across 8 NER states."))

        # 4. Seed Readings & Predictions across various dates
        now = timezone.now()

        # Reading Profiles:
        # 1. Sonapur Tunnel Area -> Worked Example from Page 16 (CRITICAL: 82.0)
        # 2. NH-10 km 32 -> HIGH (Score ~ 68.0)
        # 3. Haflong-New Haflong -> HIGH (Score ~ 58.0)
        # 4. Shillong-Dawki Road -> MODERATE (Score ~ 44.0)
        # 5. Kohima NH-29 -> MODERATE (Score ~ 38.0)
        # 6. Bomdila Pass Road -> MODERATE (Score ~ 35.0)
        # 7-12. Other locations -> LOW (Scores 8 to 22)

        readings_plan = [
            # Sonapur: 3 historical readings leading to the critical event
            {
                "loc_name": "Sonapur Tunnel Area, NH-6",
                "r24": 35.0, "r72": 80.0, "sm": 52.0, "vib": 1.2,
                "hours_ago": 48, "user": operator_user
            },
            {
                "loc_name": "Sonapur Tunnel Area, NH-6",
                "r24": 85.0, "r72": 180.0, "sm": 74.0, "vib": 3.8,
                "hours_ago": 24, "user": operator_user
            },
            # Current worked example: r24=125, r72=262.5, sm=88%, vib=6.0 -> 34+22+17+9 = 82 / 100 CRITICAL
            {
                "loc_name": "Sonapur Tunnel Area, NH-6",
                "r24": 125.0, "r72": 262.5, "sm": 88.0, "vib": 6.0,
                "hours_ago": 2, "user": operator_user
            },

            # NH-10 km 32: High risk
            {
                "loc_name": "NH-10 km 32",
                "r24": 95.0, "r72": 210.0, "sm": 78.0, "vib": 4.5,
                "hours_ago": 3, "user": operator_user
            },

            # Haflong-New Haflong: High risk
            {
                "loc_name": "Haflong-New Haflong",
                "r24": 80.0, "r72": 170.0, "sm": 72.0, "vib": 2.8,
                "hours_ago": 4, "user": operator_user
            },

            # Shillong-Dawki Road: Moderate risk
            {
                "loc_name": "Shillong-Dawki Road",
                "r24": 45.0, "r72": 110.0, "sm": 58.0, "vib": 1.8,
                "hours_ago": 6, "user": operator_user
            },

            # Kohima NH-29: Moderate risk
            {
                "loc_name": "Kohima NH-29",
                "r24": 40.0, "r72": 95.0, "sm": 50.0, "vib": 1.5,
                "hours_ago": 8, "user": operator_user
            },

            # Bomdila Pass Road: Moderate risk
            {
                "loc_name": "Bomdila Pass Road",
                "r24": 30.0, "r72": 70.0, "sm": 45.0, "vib": 2.0,
                "hours_ago": 12, "user": operator_user
            },

            # Aizawl-Hunthar Veng: Low-Moderate risk
            {
                "loc_name": "Aizawl-Hunthar Veng",
                "r24": 22.0, "r72": 55.0, "sm": 40.0, "vib": 1.0,
                "hours_ago": 5, "user": operator_user
            },

            # Ukhrul Road Slope: Low risk
            {
                "loc_name": "Ukhrul Road Slope",
                "r24": 15.0, "r72": 38.0, "sm": 35.0, "vib": 0.8,
                "hours_ago": 10, "user": operator_user
            },

            # Itanagar NH-415: Low risk
            {
                "loc_name": "Itanagar NH-415",
                "r24": 10.0, "r72": 25.0, "sm": 28.0, "vib": 0.5,
                "hours_ago": 14, "user": operator_user
            },

            # Gangtok Town Slope: Low risk
            {
                "loc_name": "Gangtok Town Slope",
                "r24": 12.0, "r72": 30.0, "sm": 30.0, "vib": 0.6,
                "hours_ago": 9, "user": operator_user
            },

            # Guwahati-Fancy Bazar Hill: Low risk
            {
                "loc_name": "Guwahati-Fancy Bazar Hill",
                "r24": 8.0, "r72": 18.0, "sm": 22.0, "vib": 0.4,
                "hours_ago": 16, "user": operator_user
            },

            # Agartala-Assam Rifles Slope: Low risk
            {
                "loc_name": "Agartala-Assam Rifles Slope",
                "r24": 5.0, "r72": 12.0, "sm": 18.0, "vib": 0.2,
                "hours_ago": 18, "user": operator_user
            },
        ]

        for item in readings_plan:
            location = created_locations[item["loc_name"]]
            reading_time = now - datetime.timedelta(hours=item["hours_ago"])

            reading, _ = SensorReading.objects.get_or_create(
                location=location,
                recorded_at=reading_time,
                defaults={
                    "rainfall_24h_mm": item["r24"],
                    "rainfall_72h_mm": item["r72"],
                    "soil_moisture_percent": item["sm"],
                    "ground_vibration": item["vib"],
                    "recorded_by": item["user"]
                }
            )

            # Evaluate with risk engine
            risk_result = evaluate_risk(
                rainfall_24h_mm=reading.rainfall_24h_mm,
                rainfall_72h_mm=reading.rainfall_72h_mm,
                soil_moisture_percent=reading.soil_moisture_percent,
                slope_angle=location.slope_angle,
                ground_vibration=reading.ground_vibration,
                location_name=location.name
            )

            pred, _ = RiskPrediction.objects.get_or_create(
                reading=reading,
                defaults={
                    "location": location,
                    "rainfall_score": risk_result["rainfall_score"],
                    "soil_score": risk_result["soil_score"],
                    "slope_score": risk_result["slope_score"],
                    "vibration_score": risk_result["vibration_score"],
                    "total_score": risk_result["total_score"],
                    "risk_level": risk_result["risk_level"],
                    "recommendation": risk_result["recommendation"],
                    "predicted_at": reading_time
                }
            )

            # Create Alerts for HIGH / CRITICAL
            if risk_result["should_alert"]:
                # Check if alert already exists for this prediction
                if not Alert.objects.filter(prediction=pred).exists():
                    status = 'ACTIVE'
                    ack_user = None
                    ack_time = None
                    note = ""

                    # Demonstrate different alert lifecycle states:
                    if location.name == "NH-10 km 32":
                        status = 'ACKNOWLEDGED'
                        ack_user = ddma_user
                        ack_time = now - datetime.timedelta(hours=2)
                        note = "DDMA Pakyong acknowledged warning. Emergency message transmitted to BRO Swastik project & local police checkposts."

                    Alert.objects.create(
                        location=location,
                        prediction=pred,
                        title=f"{risk_result['risk_level']} Landslide Threat: {location.name}",
                        message=risk_result["recommendation"],
                        level=risk_result["risk_level"],
                        status=status,
                        created_at=reading_time,
                        acknowledged_by=ack_user,
                        acknowledged_at=ack_time,
                        action_taken_note=note
                    )

        # 5. Seed Historical Landslide Incidents
        incidents_data = [
            {
                "location": created_locations["Sonapur Tunnel Area, NH-6"],
                "occurred_at": now - datetime.timedelta(days=14),
                "severity": "Major",
                "road_blocked": True,
                "description": "Massive mudslide occurred at tunnel portal following 72 hours of torrential rain. 15,000 cu.m of silt and fractured shale blocked NH-6. BRO deployed 4 excavators for 36 hours of continuous clearance.",
                "reported_by": ddma_user
            },
            {
                "location": created_locations["NH-10 km 32"],
                "occurred_at": now - datetime.timedelta(days=45),
                "severity": "Severe",
                "road_blocked": True,
                "description": "Teesta river toe cutting triggered a 70m road subsidence. Complete vehicular traffic halted between Gangtok and Siliguri for 4 days. NDRF and BRO executed temporary Bailey bridge bypass.",
                "reported_by": ddma_user
            },
            {
                "location": created_locations["Kohima NH-29"],
                "occurred_at": now - datetime.timedelta(days=90),
                "severity": "Minor",
                "road_blocked": False,
                "description": "Localized rockfall and debris slump cleared within 3 hours. Single-lane traffic maintained under traffic police supervision.",
                "reported_by": operator_user
            }
        ]

        for inc_info in incidents_data:
            LandslideIncident.objects.get_or_create(
                location=inc_info["location"],
                occurred_at=inc_info["occurred_at"],
                defaults=inc_info
            )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully with all 4 risk levels represented!"))
