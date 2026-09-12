import joblib
import pandas as pd
from ..core.config import MODEL_PATH
from ..schemas.predictor import PredictorResponse, PredictorRequest


RISK_THRESHOLD = 0.4166
HIGH_RISK_THRESHOLD = 0.70
MODEL_LOAD_ERROR = None

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    MODEL_LOAD_ERROR = {
            "error": f"Unexpected error while loading model. {e}"
        }


def predict(input_data: PredictorRequest) -> PredictorResponse:
    if MODEL_LOAD_ERROR is not None:
        raise RuntimeError(MODEL_LOAD_ERROR["error"])

    input_df = pd.DataFrame([
        input_data.model_dump()
    ])
    probabilities = model.predict_proba(input_df)

    risk_score = float(probabilities[0, 1])

    if risk_score >= HIGH_RISK_THRESHOLD:
        return PredictorResponse(
            score=risk_score,
            risk_class="high",
            threshold=RISK_THRESHOLD,
            model_version="product_v1"
        )
    elif risk_score >= RISK_THRESHOLD:
        return PredictorResponse(
            score=risk_score,
            risk_class="medium",
            threshold=RISK_THRESHOLD,
            model_version="product_v1"
        )
    else:
        return PredictorResponse(
            score=risk_score,
            risk_class="low",
            threshold=RISK_THRESHOLD,
            model_version="product_v1"
        )
