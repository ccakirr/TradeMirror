from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from ..db import get_db
from ..models.user import User
from ..core.dependencies import get_current_user
from ..services.trading_account import create_trading_account
from ..schemas.account import TradingAccountCreate, TradingAccountResponse


router = APIRouter(
    prefix="/accounts",
    tags=["trading_accounts"]
)


@router.post(
    "/",
    response_model=TradingAccountResponse
)
def create_account(
    account_data: TradingAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TradingAccountResponse:
    return create_trading_account(db, current_user, account_data)
