from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "product_blowup_risk_logistic_v1.joblib"
)
