from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.urls import reverse

from .models import MonitoringLocation, SensorReading, RiskPrediction, Alert, LandslideIncident
from .forms import ReadingForm
from .risk import (
    evaluate_risk, determine_risk_level, calculate_rainfall_score,
    calculate_soil_moisture_score, calculate_slope_score, calculate_vibration_score
)


class RiskEngineTests(TestCase):
    """
    Test cases T1-T5 verifying explainable AI risk scoring calculations and boundary behavior.
    """

    def test_t1_worked_example_score(self):
        """
        T1: Worked-example from Page 16 of Project Plan
        Sonapur Tunnel Area after heavy rain:
        Rainfall: 34 / 40
        Soil Moisture: 22 / 25
        Slope Angle: 17 / 20
        Vibration: 9 / 15
        Total = 34 + 22 + 17 + 9 = 82 / 100 -> CRITICAL
        """
        result = evaluate_risk(
            rainfall_24h_mm=125.0,
            rainfall_72h_mm=262.5,
            soil_moisture_percent=88.0,
            slope_angle=42.5,
            ground_vibration=6.0,
            location_name="Sonapur Tunnel Area, NH-6"
        )
        self.assertEqual(result['rainfall_score'], 34.0)
        self.assertEqual(result['soil_score'], 22.0)
        self.assertEqual(result['slope_score'], 17.0)
        self.assertEqual(result['vibration_score'], 9.0)
        self.assertEqual(result['total_score'], 82.0)
        self.assertEqual(result['risk_level'], 'CRITICAL')
        self.assertTrue(result['should_alert'])
        self.assertIn("CRITICAL RISK (82.0/100)", result['recommendation'])

    def test_t2_boundary_top_of_moderate(self):
        """
        T2: Boundary top of Moderate (Score = 49.0).
        Risk level must be MODERATE, and should_alert must be False.
        """
        rain_pts = calculate_rainfall_score(93.75, 0.0) # 15.0
        soil_pts = calculate_soil_moisture_score(56.0)  # 14.0
        slope_pts = calculate_slope_score(30.0)         # 12.0
        vib_pts = calculate_vibration_score(5.3333)     # 8.0
        total = round(rain_pts + soil_pts + slope_pts + vib_pts, 1)
        self.assertEqual(total, 49.0)

        level = determine_risk_level(total)
        self.assertEqual(level, 'MODERATE')

        res = evaluate_risk(93.75, 0.0, 56.0, 30.0, 5.3333)
        self.assertEqual(res['total_score'], 49.0)
        self.assertEqual(res['risk_level'], 'MODERATE')
        self.assertFalse(res['should_alert'])

    def test_t3_boundary_start_of_high(self):
        """
        T3: Boundary start of High (Score = 50.0).
        Risk level must be HIGH, and should_alert must be True.
        """
        res = evaluate_risk(93.75, 0.0, 60.0, 30.0, 5.3333)
        self.assertEqual(res['total_score'], 50.0)
        self.assertEqual(res['risk_level'], 'HIGH')
        self.assertTrue(res['should_alert'])

    def test_t4_boundary_start_of_critical(self):
        """
        T4: Boundary start of Critical (Score = 75.0).
        Risk level must be CRITICAL, and should_alert must be True.
        """
        res = evaluate_risk(150.0, 112.5, 80.0, 37.5, 6.6666)
        self.assertEqual(res['total_score'], 75.0)
        self.assertEqual(res['risk_level'], 'CRITICAL')
        self.assertTrue(res['should_alert'])

    def test_t5_low_reading_creates_no_alert(self):
        """
        T5: Low reading (Score = 10.0).
        Risk level LOW, no alert created.
        """
        res = evaluate_risk(
            rainfall_24h_mm=10.0,
            rainfall_72h_mm=0.0,
            soil_moisture_percent=15.0,
            slope_angle=12.0,
            ground_vibration=0.5
        )
        self.assertLess(res['total_score'], 25.0)
        self.assertEqual(res['risk_level'], 'LOW')
        self.assertFalse(res['should_alert'])


class WorkflowAndPermissionTests(TestCase):
    """
    Test cases T6-T9 verifying forms, auth roles, and alert lifecycle.
    """

    def setUp(self):
        # Create groups
        self.ddma_group = Group.objects.create(name='DDMA_Officer')
        self.operator_group = Group.objects.create(name='Field_Operator')

        # Create users
        self.super_admin = User.objects.create_superuser('admin', 'admin@ner.gov.in', 'Admin@123')
        self.ddma_user = User.objects.create_user('ddma_officer', 'ddma@ner.gov.in', 'Officer@123')
        self.ddma_user.groups.add(self.ddma_group)

        self.operator_user = User.objects.create_user('field_operator', 'op@ner.gov.in', 'Operator@123')
        self.operator_user.groups.add(self.operator_group)

        self.public_client = Client()
        self.operator_client = Client()
        self.operator_client.login(username='field_operator', password='Operator@123')

        self.ddma_client = Client()
        self.ddma_client.login(username='ddma_officer', password='Officer@123')

        # Create a test location with 42.5 deg slope matching worked example
        self.location = MonitoringLocation.objects.create(
            name="Sonapur Tunnel Area, NH-6",
            state="Meghalaya",
            district="East Jaintia Hills",
            latitude=25.1092,
            longitude=92.3614,
            slope_angle=42.5,
            soil_type="Sandstone & Shale",
            description="Highway tunnel zone."
        )

    def test_t6_invalid_reading_rejected(self):
        """
        T6: Invalid reading rejected (soil moisture > 100% or negative rainfall).
        """
        form_data = {
            'location': self.location.id,
            'rainfall_24h_mm': -10.0,  # Invalid negative
            'rainfall_72h_mm': 50.0,
            'soil_moisture_percent': 140.0,  # Invalid >100%
            'ground_vibration': 2.0,
            'recorded_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        form = ReadingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('rainfall_24h_mm', form.errors)
        self.assertIn('soil_moisture_percent', form.errors)

    def test_t7_public_cannot_add_reading(self):
        """
        T7: Public user cannot open Add Reading while logged out -> redirected to login.
        """
        url = reverse('reading_add')
        response = self.public_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_auto_alert_creation_on_reading_submission(self):
        """
        Verifies that submitting a reading producing High/Critical risk
        automatically saves SensorReading, RiskPrediction, and Alert!
        """
        url = reverse('reading_add')
        data = {
            'location': self.location.id,
            'rainfall_24h_mm': 125.0,
            'rainfall_72h_mm': 262.5,
            'soil_moisture_percent': 88.0,
            'ground_vibration': 6.0,
            'recorded_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        response = self.operator_client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check reading saved
        reading = SensorReading.objects.filter(location=self.location).latest('recorded_at')
        self.assertIsNotNone(reading)
        self.assertEqual(reading.recorded_by, self.operator_user)

        # Check prediction auto-created (Total 82.0 CRITICAL)
        pred = RiskPrediction.objects.get(reading=reading)
        self.assertEqual(pred.risk_level, 'CRITICAL')
        self.assertEqual(pred.total_score, 82.0)

        # Check alert auto-created
        alert = Alert.objects.filter(prediction=pred).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, 'CRITICAL')
        self.assertEqual(alert.status, 'ACTIVE')

    def test_t8_and_t9_alert_acknowledgement_lifecycle(self):
        """
        T8 & T9: Alert lifecycle:
        - Operator cannot acknowledge or close (T8)
        - DDMA officer CAN acknowledge and close (T9)
        """
        # Create active alert
        reading = SensorReading.objects.create(
            location=self.location,
            rainfall_24h_mm=120.0,
            rainfall_72h_mm=250.0,
            soil_moisture_percent=85.0,
            ground_vibration=5.5
        )
        pred = RiskPrediction.objects.create(
            location=self.location,
            reading=reading,
            rainfall_score=33.0,
            soil_score=21.0,
            slope_score=17.0,
            vibration_score=8.0,
            total_score=79.0,
            risk_level='CRITICAL',
            recommendation='Critical danger'
        )
        alert = Alert.objects.create(
            location=self.location,
            prediction=pred,
            title='Critical Threat',
            message='Immediate action required',
            level='CRITICAL',
            status='ACTIVE'
        )

        ack_url = reverse('alert_acknowledge', kwargs={'pk': alert.pk})

        # T8: Field operator tries to acknowledge -> permission denied (403)
        resp_op = self.operator_client.post(ack_url, {'action_note': 'Operator trying to ack'})
        self.assertEqual(resp_op.status_code, 403)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'ACTIVE')

        # T9: DDMA officer acknowledges
        resp_ddma = self.ddma_client.post(ack_url, {'action_note': 'DDMA initiated road closure'}, follow=True)
        self.assertEqual(resp_ddma.status_code, 200)
        alert.refresh_from_db()
        self.assertEqual(alert.status, 'ACKNOWLEDGED')
        self.assertEqual(alert.acknowledged_by, self.ddma_user)
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertIn('road closure', alert.action_taken_note)
