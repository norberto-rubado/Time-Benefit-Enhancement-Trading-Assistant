"""创新高检测与价格跟踪服务"""

from datetime import date
from sqlalchemy.orm import Session

from app.models import Stock, PriceHistory
from app.calculator import check_new_high, count_trading_days


def update_price(
    db: Session,
    stock: Stock,
    close_price: float,
    trade_date: date,
    high_price: float | None = None,
    low_price: float | None = None,
    open_price: float | None = None,
    volume: float | None = None,
) -> dict:
    """更新股票价格并检测创新高

    Returns:
        {"new_high": bool, "anchor_updated": bool, "base_n_reset": bool}
    """
    # 保存到price_history
    existing = db.query(PriceHistory).filter(
        PriceHistory.stock_id == stock.id,
        PriceHistory.trade_date == trade_date,
    ).first()

    if existing:
        existing.close_price = close_price
        existing.high_price = high_price
        existing.low_price = low_price
        existing.open_price = open_price
        existing.volume = volume
    else:
        ph = PriceHistory(
            stock_id=stock.id,
            trade_date=trade_date,
            close_price=close_price,
            high_price=high_price,
            low_price=low_price,
            open_price=open_price,
            volume=volume,
        )
        db.add(ph)

    stock.latest_close = close_price

    result = {"new_high": False, "anchor_updated": False, "base_n_reset": False}

    # 检测创新高
    is_new_high = check_new_high(stock.all_time_high, close_price)

    if is_new_high:
        stock.all_time_high = close_price
        stock.anchor_price = close_price
        stock.high_date = trade_date
        stock.base_n = 1  # 创新高当天重置为1
        result["new_high"] = True
        result["anchor_updated"] = True
        result["base_n_reset"] = True
    else:
        # 未创新高，更新base_n
        if stock.high_date:
            stock.base_n = count_trading_days(stock.high_date, trade_date)

    db.commit()
    db.refresh(stock)
    return result


def get_all_time_high(db: Session, stock_id: int) -> float | None:
    """从价格历史中获取历史最高收盘价"""
    result = db.query(PriceHistory).filter(
        PriceHistory.stock_id == stock_id
    ).order_by(PriceHistory.close_price.desc()).first()

    return result.close_price if result else None
