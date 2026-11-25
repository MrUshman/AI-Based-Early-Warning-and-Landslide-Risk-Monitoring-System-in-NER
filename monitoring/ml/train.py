import json
import os
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Base directories
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACTS_DIR / "landslide_rf_model.joblib"
METRICS_PATH = ARTIFACTS_DIR / "model_metrics.json"
DATASET_PATH = ARTIFACTS_DIR / "synthetic_ner_landslide_dataset.csv"

SOIL_MAP = {"clay": 0, "loamy": 1, "sandy": 2, "rocky": 3, "silt": 4}
REV_SOIL_MAP = {v: k for k, v in SOIL_MAP.items()}
CLASSES = ["Low", "Moderate", "High", "Critical"]


def generate_synthetic_ner_data(n_samples=2500, random_seed=42):
    """
    Generate synthetic geotechnical & hydrological dataset based on GSI
    (Geological Survey of India) and IMD landslide threshold models for the NER Himalayas.
    """
    rng = np.random.RandomState(random_seed)

    # 1. Rainfall 24h (mm) - Gamma distributed with typical monsoon bursts
    rain_24h = rng.gamma(shape=2.0, scale=35.0, size=n_samples)
    rain_24h = np.clip(rain_24h, 0.0, 350.0)

    # 2. Rainfall 72h (mm) - Cumulative monsoon rainfall
    rain_72h = rain_24h * rng.uniform(1.3, 2.8, size=n_samples) + rng.exponential(scale=20.0, size=n_samples)
    rain_72h = np.clip(rain_72h, 0.0, 650.0)

    # 3. Soil Moisture (%) - Correlated with cumulative rainfall
    base_moisture = 20.0 + (rain_72h / 650.0) * 65.0 + rng.normal(0, 8.0, size=n_samples)
    soil_moisture = np.clip(base_moisture, 15.0, 98.0)

    # 4. Slope angle (degrees) - NER hills range 10° to 65°
    slope_angle = rng.normal(36.0, 11.0, size=n_samples)
    slope_angle = np.clip(slope_angle, 8.0, 68.0)

    # 5. Ground vibration / seismic activity (0 - 10 scale)
    vibration = rng.exponential(scale=1.2, size=n_samples)
    vibration = np.clip(vibration, 0.0, 9.5)

    # 6. Elevation (m) - NER terrain (150m to 3500m)
    elevation = rng.uniform(180.0, 2800.0, size=n_samples)

    # 7. Soil Type (0: clay, 1: loamy, 2: sandy, 3: rocky, 4: silt)
    soil_types = rng.choice([0, 1, 2, 3, 4], size=n_samples, p=[0.25, 0.30, 0.15, 0.15, 0.15])

    # Soil stability factor (clay and silt lose shear strength faster when saturated)
    soil_weight = np.array([1.25, 1.0, 1.1, 0.85, 1.2])
    soil_factor = soil_weight[soil_types]

    # Geotechnical Landslide Factor of Safety (FS) approximation:
    # High rainfall, high moisture, steep slope, and high vibration drastically increase probability
    latent_risk = (
        (rain_24h / 150.0) * 0.35 +
        (rain_72h / 300.0) * 0.15 +
        ((soil_moisture - 30.0) / 50.0).clip(0) * 0.25 * soil_factor +
        ((slope_angle - 20.0) / 25.0).clip(0) * 0.20 +
        (vibration / 10.0) * 0.15 +
        rng.normal(0, 0.06, size=n_samples)  # Real-world environmental noise
    )

    # Map continuous latent risk to 4 distinct classes
    # 0: Low (<0.32), 1: Moderate (0.32 - 0.58), 2: High (0.58 - 0.82), 3: Critical (>=0.82)
    labels = np.zeros(n_samples, dtype=int)
    labels[latent_risk >= 0.32] = 1
    labels[latent_risk >= 0.58] = 2
    labels[latent_risk >= 0.82] = 3

    features = np.column_stack([
        rain_24h,
        rain_72h,
        soil_moisture,
        slope_angle,
        vibration,
        elevation,
        soil_types,
    ])

    return features, labels


def train_and_evaluate():
    print("Generating synthetic NER geotechnical dataset...")
    X, y = generate_synthetic_ner_data(n_samples=3000, random_seed=42)

    feature_names = [
        "rainfall_24h_mm",
        "rainfall_72h_mm",
        "soil_moisture_pct",
        "slope_angle",
        "ground_vibration",
        "elevation_m",
        "soil_type_code",
    ]

    # Save CSV dataset for academic documentation
    header = ",".join(feature_names + ["risk_class", "risk_level"])
    csv_rows = []
    for row, label in zip(X, y):
        row_str = ",".join(f"{val:.2f}" for val in row)
        csv_rows.append(f"{row_str},{label},{CLASSES[label]}")

    DATASET_PATH.write_text(header + "\n" + "\n".join(csv_rows), encoding="utf-8")
    print(f"Dataset saved to {DATASET_PATH}")

    # Train / Test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, target_names=CLASSES, output_dict=True)

    # Feature importance
    importances = model.feature_importances_.tolist()
    feature_imp_dict = {
        name: round(float(imp) * 100, 2)
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])
    }

    # Save trained model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    # Save metrics JSON
    metrics = {
        "model_name": "RandomForestClassifier",
        "n_estimators": 120,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(float(acc) * 100, 2),
        "confusion_matrix": cm,
        "classes": CLASSES,
        "feature_importances": feature_imp_dict,
        "classification_report": {
            cls_name: {
                "precision": round(report[cls_name]["precision"] * 100, 1),
                "recall": round(report[cls_name]["recall"] * 100, 1),
                "f1_score": round(report[cls_name]["f1-score"] * 100, 1),
                "support": report[cls_name]["support"],
            }
            for cls_name in CLASSES
        },
        "macro_avg_f1": round(report["macro avg"]["f1-score"] * 100, 1),
    }

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Metrics saved to {METRICS_PATH}")
    print(f"Training Complete! Test Accuracy: {metrics['accuracy']}%")
    return metrics


if __name__ == "__main__":
    train_and_evaluate()
