"""每日汇总路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Position, PositionStatus
from app.schemas import DashboardResponse, DashboardStockSummary, LadderStep
from app.services.strategy import compute_ladder

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardResponse)
def get_summary(db: Session = Depends(get_db)):
    """获取每日汇总"""
    stocks = db.query(Stock).order_by(Stock.id).all()

    total_held = 0
    stock_summaries = []

    for stock in stocks:
        ladder = compute_ladder(db, stock)
        steps = []
        held_count = 0
        next_action = None
        next_action_price = None
        next_action_slot = None
        next_action_direction = None

        for s in ladder.get("steps", []):
            step = LadderStep(
                slot=s["slot"],
                status=s["status"],
                buy_price=s.get("buy_price"),
                sell_price=s.get("sell_price"),
                next_buy_price=s.get("next_buy_price") or s.get("estimated_buy_price"),
                holding_days=s.get("holding_days", 0),
                shares=s.get("shares", 0),
                buy_date=s.get("buy_date"),
                profit_rate=s.get("profit_rate"),
            )
            steps.append(step)

            if s["status"] == "held":
                held_count += 1
                # 检查是否可以卖出（非底仓）
                if s["slot"] > 1 and stock.latest_close and s.get("sell_price"):
                    if stock.latest_close >= s["sell_price"]:
                        next_action = f"可卖出第{s['slot']}笔"
                        next_action_price = s["sell_price"]
                        next_action_slot = s["slot"]
                        next_action_direction = "sell"

            elif s["status"] == "empty" and next_action is None:
                # 找到第一个空仓位的预估买入价
                buy_p = s.get("next_buy_price") or s.get("estimated_buy_price")
                if buy_p and stock.latest_close and stock.latest_close <= buy_p:
                    next_action = f"可买入第{s['slot']}笔"
                    next_action_price = buy_p
                    next_action_slot = s["slot"]
                    next_action_direction = "buy"
                elif buy_p and not next_action:
                    next_action = f"等待第{s['slot']}笔买入"
                    next_action_price = buy_p
                    next_action_slot = s["slot"]
                    next_action_direction = "buy"

        total_held += held_count

        stock_summaries.append(DashboardStockSummary(
            stock_id=stock.id,
            stock_code=stock.code,
            stock_name=stock.name,
            latest_close=stock.latest_close,
            anchor_price=stock.anchor_price,
            base_n=stock.base_n,
            held_count=held_count,
            positions=steps,
            next_action=next_action,
            next_action_price=next_action_price,
            next_action_slot=next_action_slot,
            next_action_direction=next_action_direction,
        ))

    return DashboardResponse(
        total_stocks=len(stocks),
        total_held_positions=total_held,
        stocks=stock_summaries,
    )
