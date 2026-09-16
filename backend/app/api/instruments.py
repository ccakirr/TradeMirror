from fastapi import APIRouter

from ..core.instruments import list_instruments
from ..schemas.instrument import InstrumentResponse


router = APIRouter(
    prefix="/instruments",
    tags=["instruments"]
)


@router.get(
    "/",
    response_model=list[InstrumentResponse],
)
def get_instruments() -> list[InstrumentResponse]:
    """Reference data: no user rows involved, so no token is required."""
    return [
        InstrumentResponse.model_validate(instrument)
        for instrument in list_instruments()
    ]
