import joblib
import pandas as pd

from ..core.config import settings
from ..schemas.predictor import PredictorRequest, PredictorResponse


MODEL_PATH = settings.model_path
RISK_THRESHOLD = 0.4166
HIGH_RISK_THRESHOLD = 0.70
MODEL_LOAD_ERROR = None

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    MODEL_LOAD_ERROR = {
        "error": f"Unexpected error while loading model. {e}"
    }


def classify_risk(risk_score: float) -> str:
    if risk_score >= HIGH_RISK_THRESHOLD:
        return "high"

    if risk_score >= RISK_THRESHOLD:
        return "medium"

    return "low"


def predict(input_data: PredictorRequest) -> PredictorResponse:
    if MODEL_LOAD_ERROR is not None:
        raise RuntimeError(MODEL_LOAD_ERROR["error"])

    input_df = pd.DataFrame([
        input_data.model_dump()
    ])

    probabilities = model.predict_proba(input_df)
    risk_score = float(probabilities[0, 1])
    risk_class = classify_risk(risk_score)

    return PredictorResponse(
        score=risk_score,
        risk_class=risk_class,
        threshold=RISK_THRESHOLD,
        model_version="product_v1"
    )
