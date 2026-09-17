from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..models.user import User
from ..core.dependencies import get_current_user
from ..schemas.trade import TradeCreate, TradeResponse, TradeClose
from ..schemas.predictor import (
    RiskAssessmentCreate,
    RiskAssessmentResponse,
)
from ..services.trading_account import (
    create_trading_account,
    list_trading_accounts,
    save_risk_profile,
    get_risk_profile,
)
from ..services.trade import create_trade as create_trade_service
from ..services.trade import close_trade as close_trade_service, list_trades
from ..services.trade import get_trade as get_trade_service
from ..services.trade import TradeValidationError
from ..services.risk_assessment import (
    create_risk_assessment,
    list_risk_assessments,
)
from ..services.risk_report import get_risk_report
from ..schemas.risk_report import RiskReportResponse
from ..schemas.account import (
    TradingAccountCreate,
    TradingAccountResponse,
    TradingAccountRiskProfileCreate,
    TradingAccountRiskProfileResponse,
)
from ..schemas.plan import TradingPlanCreate, TradingPlanResponse
from ..services.trading_plan import create_trading_plan, list_trading_plans


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


@router.get(
    "/",
    response_model=list[TradingAccountResponse],
)
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradingAccountResponse]:
    return list_trading_accounts(db, current_user)


@router.put(
    "/{account_id}/risk-profile",
    response_model=TradingAccountRiskProfileResponse,
)
def update_account_risk_profile(
    account_id: UUID,
    profile_data: TradingAccountRiskProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingAccountRiskProfileResponse:
    try:
        return save_risk_profile(db, current_user, account_id, profile_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/risk-profile",
    response_model=TradingAccountRiskProfileResponse,
)
def get_account_risk_profile(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingAccountRiskProfileResponse:
    try:
        return get_risk_profile(db, current_user, account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{account_id}/plans",
    response_model=TradingPlanResponse,
    status_code=201,
)
def create_account_plan(
    account_id: UUID,
    plan_data: TradingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradingPlanResponse:
    try:
        return create_trading_plan(db, current_user, account_id, plan_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/plans",
    response_model=list[TradingPlanResponse],
)
def get_account_plans(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradingPlanResponse]:
    try:
        return list_trading_plans(db, current_user, account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{account_id}/trades",
    response_model=TradeResponse,
    status_code=201,
)
def create_account_trade(
    account_id: UUID,
    trade_data: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TradeResponse:
    try:
        return create_trade_service(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_data=trade_data,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )


@router.get(
    "/{account_id}/trades",
    response_model=list[TradeResponse],
)
def get_account_trades(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TradeResponse]:
    try:
        return list_trades(db, current_user, account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/trades/{trade_id}",
    response_model=TradeResponse,
)
def get_account_trade(
    account_id: UUID,
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeResponse:
    try:
        return get_trade_service(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_id=trade_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{account_id}/trades/{trade_id}/close",
    response_model=TradeResponse,
)
def close_account_trade(
    account_id: UUID,
    trade_id: UUID,
    trade_data: TradeClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TradeResponse:
    try:
        return close_trade_service(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_id=trade_id,
            trade_data=trade_data,
        )
    except TradeValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{account_id}/trades/{trade_id}/risk-assessments",
    response_model=RiskAssessmentResponse,
    status_code=201,
)
def create_trade_risk_assessment(
    account_id: UUID,
    trade_id: UUID,
    assessment_data: RiskAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentResponse:
    try:
        return create_risk_assessment(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_id=trade_id,
            assessment_data=assessment_data,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/trades/{trade_id}/risk-assessments",
    response_model=list[RiskAssessmentResponse],
)
def get_trade_risk_assessments(
    account_id: UUID,
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RiskAssessmentResponse]:
    try:
        return list_risk_assessments(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_id=trade_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{account_id}/trades/{trade_id}/risk-report",
    response_model=RiskReportResponse,
)
def get_trade_risk_report(
    account_id: UUID,
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskReportResponse:
    try:
        return get_risk_report(
            db=db,
            current_user=current_user,
            account_id=account_id,
            trade_id=trade_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
