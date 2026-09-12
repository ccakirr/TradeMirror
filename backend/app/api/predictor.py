from fastapi import APIRouter, HTTPException
from ..schemas.predictor import PredictorResponse, PredictorRequest
from ..services.predictor import predict


router = APIRouter(
    prefix="/predict",
    tags=["predict"]
)


@router.post("/", response_model=PredictorResponse)
def predict_risk(request: PredictorRequest) -> PredictorResponse:
    try:
        predicted_result = predict(request)
        return predicted_result
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Risk assessment could not be completed."
        )
