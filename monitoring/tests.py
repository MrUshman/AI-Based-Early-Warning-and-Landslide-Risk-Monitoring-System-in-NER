import json
from django.test import Client, TestCase
from django.urls import reverse
from .models import Alert, MonitoringLocation, RiskPrediction, SensorReading
from .risk_engine import get_model_metadata, predict_risk


class RiskEngineTests(TestCase):
    def test_dry_stable_conditions_are_low(self):
        result = predict_risk(
            rainfall_24h_mm=5,
            rainfall_72h_mm=15,
            soil_moisture_pct=25,
            slope_angle=15,
            ground_vibration=0,
            elevation_m=400,
            soil_type="loamy",
        )
        self.assertEqual(result["risk_level"], "Low")
        self.assertLess(result["risk_score"], 25)

    def test_extreme_conditions_are_critical(self):
        result = predict_risk(
            rainfall_24h_mm=180,
            rainfall_72h_mm=360,
            soil_moisture_pct=92,
            slope_angle=52,
            ground_vibration=6.5,
            elevation_m=1200,
            soil_type="clay",
        )
        self.assertEqual(result["risk_level"], "Critical")
        self.assertGreaterEqual(result["risk_score"], 75)

    def test_score_never_exceeds_100(self):
        result = predict_risk(
            rainfall_24h_mm=500,
            rainfall_72h_mm=900,
            soil_moisture_pct=100,
            slope_angle=90,
            ground_vibration=10,
        )
        self.assertLessEqual(result["risk_score"], 100)

    def test_model_metadata_returns_valid_metrics(self):
        meta = get_model_metadata()
        self.assertIn("accuracy", meta)
        self.assertIn("feature_importances", meta)
        self.assertGreater(meta["accuracy"], 50.0)


class LandslideViewsAndAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.location = MonitoringLocation.objects.create(
            name="NH-10 Highway, km 32",
            state="Sikkim",
            district="Gangtok",
            latitude=27.25,
            longitude=88.50,
            elevation_m=1250,
            slope_angle=42,
            soil_type="clay",
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Regional Geotechnical Command Center")
        self.assertContains(response, "Geospatial GIS Surveillance Map")

    def test_calculator_view_get_and_post(self):
        get_res = self.client.get(reverse("risk_calculator"))
        self.assertEqual(get_res.status_code, 200)

        post_res = self.client.post(reverse("risk_calculator"), {
            "rainfall_24h_mm": 150,
            "rainfall_72h_mm": 300,
            "soil_moisture_pct": 85,
            "slope_angle": 45,
            "ground_vibration": 4.0,
        })
        self.assertEqual(post_res.status_code, 200)
        self.assertContains(post_res, "Critical Threat")

    def test_model_metrics_view(self):
        response = self.client.get(reverse("model_metrics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Confusion Matrix")
        self.assertContains(response, "RandomForestClassifier")

    def test_api_locations_endpoint(self):
        response = self.client.get(reverse("api_locations"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["count"], 1)
        self.assertEqual(data["locations"][0]["name"], "NH-10 Highway, km 32")

    def test_api_create_reading_endpoint(self):
        payload = {
            "location_id": self.location.id,
            "rainfall_24h_mm": 140.0,
            "rainfall_72h_mm": 280.0,
            "soil_moisture_pct": 86.0,
            "ground_vibration": 3.5,
            "temperature_c": 22.0,
            "humidity_pct": 85.0,
        }
        response = self.client.post(
            reverse("api_create_reading"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("risk_level", data)
        self.assertTrue(data["alert_triggered"])

        # Check that Alert was generated
        self.assertTrue(Alert.objects.filter(location=self.location).exists())

    def test_export_alerts_csv(self):
        response = self.client.get(reverse("export_alerts_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_custom_404_view(self):
        response = self.client.get("/non-existent-page-url/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Station / Corridor Not Found", status_code=404)

    def test_favicon_redirect(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/static/favicon.svg")

    def test_mobile_offcanvas_menu_in_base(self):
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "id=\"mobileOffcanvas\"")
        self.assertContains(response, "tel:1077")
        self.assertContains(response, "mailto:controlroom-ner@disaster.gov.in")

