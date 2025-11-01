from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/portfolio", response_model=schemas.PortfolioSummary)
def get_portfolio_summary(db: Session = Depends(get_db)) -> schemas.PortfolioSummary:
    return crud.portfolio_summary(db)


@router.get("/team", response_model=list[schemas.UtilizationBreakdown])
def get_team_utilization(db: Session = Depends(get_db)) -> list[schemas.UtilizationBreakdown]:
    return crud.team_utilization(db)
