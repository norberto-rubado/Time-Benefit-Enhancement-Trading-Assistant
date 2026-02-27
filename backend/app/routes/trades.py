"""交易记录路由"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, Stock, TradeDirection
from app.schemas import TradeLogResponse
from app.services.strategy import void_buy_trade, void_sell_trade

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/", response_model=list[TradeLogResponse])
def list_trades(
    stock_id: int | None = Query(None),
    include_voided: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取交易记录列表"""
    query = db.query(Trade).join(Stock)

    if stock_id:
        query = query.filter(Trade.stock_id == stock_id)

    if not include_voided:
        query = query.filter(Trade.is_voided == False)

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
            is_voided=t.is_voided,
            voided_at=t.voided_at,
            created_at=t.created_at,
        ))

    return result


@router.get("/count")
def count_trades(
    stock_id: int | None = Query(None),
    include_voided: bool = Query(False),
    db: Session = Depends(get_db),
):
    """获取交易记录总数"""
    query = db.query(Trade)
    if stock_id:
        query = query.filter(Trade.stock_id == stock_id)
    if not include_voided:
        query = query.filter(Trade.is_voided == False)
    return {"count": query.count()}


@router.post("/{trade_id}/void")
def void_trade(
    trade_id: int,
    db: Session = Depends(get_db),
):
    """作废交易记录"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    if trade.is_voided:
        raise HTTPException(status_code=400, detail="该交易记录已作废")

    try:
        if trade.direction == TradeDirection.BUY:
            void_buy_trade(db, trade)
        else:
            void_sell_trade(db, trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 标记交易为已作废
    trade.is_voided = True
    trade.voided_at = datetime.now()
    db.commit()

    return {"message": "交易记录已作废", "trade_id": trade_id}
