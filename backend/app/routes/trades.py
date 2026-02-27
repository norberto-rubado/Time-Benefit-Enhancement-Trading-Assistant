"""交易记录路由"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, Stock
from app.schemas import TradeLogResponse

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/", response_model=list[TradeLogResponse])
def list_trades(
    stock_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取交易记录列表"""
    query = db.query(Trade).join(Stock)

    if stock_id:
        query = query.filter(Trade.stock_id == stock_id)

    trades = query.order_by(Trade.trade_date.desc(), Trade.id.desc()).offset(offset).limit(limit).all()

    result = []
    for t in trades:
        result.append(TradeLogResponse(
            id=t.id,
            stock_id=t.stock_id,
            stock_code=t.stock.code,
            stock_name=t.stock.name,
            direction=t.direction,
            slot=t.slot,
            price=t.price,
            shares=t.shares,
            trade_date=t.trade_date,
            note=t.note,
            created_at=t.created_at,
        ))

    return result


@router.get("/count")
def count_trades(
    stock_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """获取交易记录总数"""
    query = db.query(Trade)
    if stock_id:
        query = query.filter(Trade.stock_id == stock_id)
    return {"count": query.count()}
