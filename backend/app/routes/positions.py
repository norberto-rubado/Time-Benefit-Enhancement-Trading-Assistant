"""仓位管理+阶梯计算路由"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Trade, TradeDirection
from app.schemas import TradeCreate, LadderResponse, LadderStep
from app.services.strategy import compute_ladder, execute_buy, execute_sell

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("/{stock_id}/ladder", response_model=LadderResponse)
def get_ladder(stock_id: int, db: Session = Depends(get_db)):
    """获取完整阶梯计算结果"""
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    result = compute_ladder(db, stock)

    steps = []
    for s in result["steps"]:
        steps.append(LadderStep(
            slot=s["slot"],
            status=s["status"],
            buy_price=s.get("buy_price"),
            sell_price=s.get("sell_price"),
            next_buy_price=s.get("next_buy_price") or s.get("estimated_buy_price"),
            holding_days=s.get("holding_days", 0),
            shares=s.get("shares", 0),
            buy_date=s.get("buy_date"),
            profit_rate=s.get("profit_rate"),
        ))

    return LadderResponse(
        stock_id=result["stock_id"],
        stock_code=result["stock_code"],
        stock_name=result["stock_name"],
        anchor_price=result["anchor_price"],
        base_n=result["base_n"],
        R=result["R"],
        D=result["D"],
        latest_close=result["latest_close"],
        steps=steps,
    )


@router.post("/{stock_id}/buy")
def buy_position(stock_id: int, slot: int, data: TradeCreate, db: Session = Depends(get_db)):
    """记录买入操作"""
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    if slot < 1 or slot > 4:
        raise HTTPException(status_code=400, detail="仓位笔数必须在1-4之间")

    trade_date = data.trade_date or date.today()

    pos = execute_buy(db, stock, slot, data.price, data.shares, trade_date)

    # 记录交易日志
    trade = Trade(
        stock_id=stock_id,
        direction=TradeDirection.BUY,
        slot=slot,
        price=data.price,
        shares=data.shares,
        trade_date=trade_date,
        note=data.note,
    )
    db.add(trade)
    db.commit()

    return {"message": "买入成功", "position_id": pos.id}


@router.post("/{stock_id}/sell")
def sell_position(stock_id: int, slot: int, data: TradeCreate, db: Session = Depends(get_db)):
    """记录卖出操作"""
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    if slot < 1 or slot > 4:
        raise HTTPException(status_code=400, detail="仓位笔数必须在1-4之间")

    trade_date = data.trade_date or date.today()

    try:
        pos = execute_sell(db, stock, slot, data.price, data.shares, trade_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 记录交易日志
    trade = Trade(
        stock_id=stock_id,
        direction=TradeDirection.SELL,
        slot=slot,
        price=data.price,
        shares=data.shares,
        trade_date=trade_date,
        note=data.note,
    )
    db.add(trade)
    db.commit()

    return {"message": "卖出成功", "position_id": pos.id}
