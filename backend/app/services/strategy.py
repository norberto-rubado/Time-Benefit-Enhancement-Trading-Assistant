"""策略编排服务 - 协调计算引擎和数据层"""

from datetime import date
from sqlalchemy.orm import Session

from app.models import Stock, Position, Setting, Trade, TradeDirection, PositionStatus
from app.calculator import (
    calculate_full_ladder,
    count_trading_days,
)
from app.config import settings as app_settings


def get_strategy_params(db: Session) -> dict:
    """获取策略参数"""
    params = {
        "R": app_settings.DEFAULT_R,
        "D": app_settings.DEFAULT_D,
        "min_N": app_settings.DEFAULT_MIN_N,
    }
    db_settings = db.query(Setting).all()
    for s in db_settings:
        if s.key == "R":
            params["R"] = float(s.value)
        elif s.key == "D":
            params["D"] = float(s.value)
        elif s.key == "min_N":
            params["min_N"] = int(s.value)
    return params


def get_held_positions(db: Session, stock_id: int) -> list[dict]:
    """获取已持仓位信息"""
    positions = db.query(Position).filter(
        Position.stock_id == stock_id,
        Position.status == PositionStatus.HELD,
    ).order_by(Position.slot).all()

    today = date.today()
    result = []
    for p in positions:
        holding_days = p.holding_days
        if p.buy_date:
            holding_days = count_trading_days(p.buy_date, today)
            # 同步更新数据库中的holding_days
            p.holding_days = holding_days

        result.append({
            "slot": p.slot,
            "buy_price": p.buy_price,
            "holding_days": holding_days,
            "shares": p.shares,
            "buy_date": p.buy_date,
        })

    if result:
        db.commit()

    return result


def compute_ladder(db: Session, stock: Stock) -> dict:
    """计算完整阶梯"""
    params = get_strategy_params(db)
    held = get_held_positions(db, stock.id)

    anchor = stock.anchor_price or stock.latest_close or 0
    if anchor <= 0:
        return {
            "stock_id": stock.id,
            "stock_code": stock.code,
            "stock_name": stock.name,
            "anchor_price": None,
            "base_n": stock.base_n,
            "R": params["R"],
            "D": params["D"],
            "latest_close": stock.latest_close,
            "steps": [],
        }

    steps = calculate_full_ladder(
        anchor_price=anchor,
        R=params["R"],
        base_N=stock.base_n,
        D=params["D"],
        min_N=params["min_N"],
        held_positions=held,
    )

    # 更新positions表中的计算字段
    _sync_calculated_prices(db, stock.id, steps)

    return {
        "stock_id": stock.id,
        "stock_code": stock.code,
        "stock_name": stock.name,
        "anchor_price": anchor,
        "base_n": stock.base_n,
        "R": params["R"],
        "D": params["D"],
        "latest_close": stock.latest_close,
        "steps": steps,
    }


def _sync_calculated_prices(db: Session, stock_id: int, steps: list[dict]):
    """同步计算结果到positions表"""
    for step in steps:
        slot = step["slot"]
        pos = db.query(Position).filter(
            Position.stock_id == stock_id,
            Position.slot == slot,
        ).first()

        if not pos:
            pos = Position(stock_id=stock_id, slot=slot)
            db.add(pos)

        pos.calculated_sell_price = step.get("sell_price")
        # 对于空仓位，存储预估买入价
        if step["status"] == "empty":
            pos.calculated_buy_price = step.get("next_buy_price") or step.get("estimated_buy_price")
        else:
            pos.calculated_buy_price = step.get("next_buy_price")

    db.commit()


def execute_buy(
    db: Session, stock: Stock, slot: int, price: float, shares: int, trade_date: date
) -> Position:
    """执行买入操作"""
    pos = db.query(Position).filter(
        Position.stock_id == stock.id,
        Position.slot == slot,
    ).first()

    if not pos:
        pos = Position(stock_id=stock.id, slot=slot)
        db.add(pos)

    pos.status = PositionStatus.HELD
    pos.buy_price = price
    pos.buy_date = trade_date
    pos.shares = (pos.shares or 0) + shares
    pos.holding_days = 1

    # 如果是第一笔且没有锚点价，设置锚点价
    if slot == 1 and not stock.anchor_price:
        stock.anchor_price = price
        stock.all_time_high = price
        stock.high_date = trade_date

    db.commit()
    db.refresh(pos)
    return pos


def execute_sell(
    db: Session, stock: Stock, slot: int, price: float, shares: int, trade_date: date
) -> Position:
    """执行卖出操作"""
    pos = db.query(Position).filter(
        Position.stock_id == stock.id,
        Position.slot == slot,
    ).first()

    if not pos or pos.status != PositionStatus.HELD:
        raise ValueError(f"仓位 {slot} 未持仓，无法卖出")

    if slot == 1:
        raise ValueError("第1笔底仓不可卖出")

    pos.shares = max(0, (pos.shares or 0) - shares)
    if pos.shares <= 0:
        pos.status = PositionStatus.EMPTY
        pos.buy_price = None
        pos.buy_date = None
        pos.shares = 0
        pos.holding_days = 0

    db.commit()
    db.refresh(pos)
    return pos


def void_buy_trade(db: Session, trade: Trade) -> None:
    """作废买入交易记录并回滚仓位

    Args:
        trade: 要作废的买入交易记录

    Raises:
        ValueError: 存在后续未作废的卖出记录，或其他不允许作废的情况
    """
    # 检查该 slot 是否有后续未作废的卖出记录
    later_sells = db.query(Trade).filter(
        Trade.stock_id == trade.stock_id,
        Trade.slot == trade.slot,
        Trade.direction == TradeDirection.SELL,
        Trade.is_voided == False,
        Trade.id > trade.id,
    ).count()

    if later_sells > 0:
        raise ValueError("请先作废对应的卖出记录")

    # 查找该 slot 更早的未作废买入记录（恢复到前一次买入状态）
    prev_buy = db.query(Trade).filter(
        Trade.stock_id == trade.stock_id,
        Trade.slot == trade.slot,
        Trade.direction == TradeDirection.BUY,
        Trade.is_voided == False,
        Trade.id < trade.id,
    ).order_by(Trade.id.desc()).first()

    pos = db.query(Position).filter(
        Position.stock_id == trade.stock_id,
        Position.slot == trade.slot,
    ).first()

    if pos:
        if prev_buy:
            # 恢复到前一次买入状态
            pos.status = PositionStatus.HELD
            pos.buy_price = prev_buy.price
            pos.shares = prev_buy.shares
            pos.buy_date = prev_buy.trade_date
            pos.holding_days = count_trading_days(prev_buy.trade_date, date.today())
        else:
            # 无前序买入 → 清空仓位
            pos.status = PositionStatus.EMPTY
            pos.buy_price = None
            pos.buy_date = None
            pos.shares = 0
            pos.holding_days = 0

    db.commit()


def void_sell_trade(db: Session, trade: Trade) -> None:
    """作废卖出交易记录并恢复仓位

    Args:
        trade: 要作废的卖出交易记录

    Raises:
        ValueError: 存在后续未作废的买入记录，或找不到原始买入记录
    """
    # 检查该 slot 是否有后续未作废的买入记录（重新买入）
    later_buys = db.query(Trade).filter(
        Trade.stock_id == trade.stock_id,
        Trade.slot == trade.slot,
        Trade.direction == TradeDirection.BUY,
        Trade.is_voided == False,
        Trade.id > trade.id,
    ).count()

    if later_buys > 0:
        raise ValueError("请先作废对应的买入记录")

    # 查找该 slot 最近一次未作废的买入记录（在此卖出之前的）
    original_buy = db.query(Trade).filter(
        Trade.stock_id == trade.stock_id,
        Trade.slot == trade.slot,
        Trade.direction == TradeDirection.BUY,
        Trade.is_voided == False,
        Trade.id < trade.id,
    ).order_by(Trade.id.desc()).first()

    if not original_buy:
        raise ValueError("未找到对应的买入记录，无法恢复仓位")

    pos = db.query(Position).filter(
        Position.stock_id == trade.stock_id,
        Position.slot == trade.slot,
    ).first()

    if pos:
        # 恢复仓位到买入状态
        pos.status = PositionStatus.HELD
        pos.buy_price = original_buy.price
        pos.shares = original_buy.shares
        pos.buy_date = original_buy.trade_date
        pos.holding_days = count_trading_days(original_buy.trade_date, date.today())

    db.commit()
