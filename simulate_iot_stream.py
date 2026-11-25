"""
IoT Sensor Telemetry Simulator
==============================
Simulates remote field IoT stations across North-East India (e.g. rain gauges,
piezometers, tiltmeters) pushing periodic telemetry packets to the Django REST API.

Usage:
    python simulate_iot_stream.py [--count 5] [--interval 2] [--location 1]
"""

import argparse
import random
import time
import requests

API_ENDPOINT = "http://127.0.0.1:8000/api/readings/"
LOCATIONS_ENDPOINT = "http://127.0.0.1:8000/api/locations/"


def run_simulation(count=10, interval=2.5, target_location=None):
    print("=" * 65)
    print("   📡 LANDSLIDE EARLY WARNING SYSTEM - IoT TELEMETRY STREAM   ")
    print("=" * 65)
    print(f"Target API: {API_ENDPOINT}")
    print(f"Polling Interval: {interval}s | Packets to send: {count}\n")

    # Fetch available locations from API
    try:
        resp = requests.get(LOCATIONS_ENDPOINT, timeout=3)
        if resp.status_code == 200:
            locations = resp.json().get("locations", [])
            print(f"Connected to Central Server! Detected {len(locations)} active monitoring stations.")
        else:
            locations = [{"id": 1, "name": "NH-10 Highway, km 32", "state": "Sikkim"}]
    except Exception:
        print("[Notice] Could not query locations API (server might be booting). Defaulting to Station #1.")
        locations = [{"id": 1, "name": "NH-10 Highway, km 32", "state": "Sikkim"}]

    for i in range(1, count + 1):
        if target_location:
            loc = next((l for l in locations if l["id"] == target_location), locations[0])
        else:
            loc = random.choice(locations)

        # Generate realistic monsoon sensor reading (intermittent high spikes)
        is_surge = (random.random() < 0.3)  # 30% chance of critical rain surge
        rain_24 = round(random.uniform(130.0, 220.0) if is_surge else random.uniform(10.0, 85.0), 1)
        rain_72 = round(rain_24 * random.uniform(1.8, 2.7), 1)
        soil_moisture = round(random.uniform(75.0, 94.0) if is_surge else random.uniform(35.0, 68.0), 1)
        vibration = round(random.uniform(2.5, 6.0) if is_surge else random.uniform(0.1, 1.5), 1)
        temp = round(random.uniform(16.0, 26.0), 1)
        humidity = round(random.uniform(70.0, 98.0), 1)

        payload = {
            "location_id": loc["id"],
            "rainfall_24h_mm": rain_24,
            "rainfall_72h_mm": rain_72,
            "soil_moisture_pct": soil_moisture,
            "ground_vibration": vibration,
            "temperature_c": temp,
            "humidity_pct": humidity,
        }

        try:
            res = requests.post(API_ENDPOINT, json=payload, timeout=4)
            if res.status_code == 201:
                data = res.json()
                badge = f"🚨 {data['risk_level'].upper()}" if data["alert_triggered"] else f"✅ {data['risk_level']}"
                print(
                    f"[{i:02d}/{count:02d}] Sent -> Station: {loc['name']:<26} | "
                    f"Rain24: {rain_24:>5}mm | Soil: {soil_moisture:>4}% | "
                    f"Score: {data['risk_score']:>4.0f}/100 | Status: {badge}"
                )
                if data["alert_triggered"]:
                    print(f"       >> ALERT ISSUED: {data['recommendation'][:75]}...")
            else:
                print(f"[{i:02d}/{count:02d}] Failed: HTTP {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[{i:02d}/{count:02d}] Connection Error: {e} (Is `python manage.py runserver` running?)")

        if i < count:
            time.sleep(interval)

    print("\n[Done] Telemetry simulation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate IoT sensor stream to Landslide EWS API")
    parser.add_argument("--count", type=int, default=8, help="Number of telemetry packets to send")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between packets")
    parser.add_argument("--location", type=int, default=None, help="Specific station ID to target")
    args = parser.parse_args()

    run_simulation(count=args.count, interval=args.interval, target_location=args.location)
