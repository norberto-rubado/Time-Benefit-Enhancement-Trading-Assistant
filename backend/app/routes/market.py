"""行情数据路由"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock
from app.schemas import PriceInput
from app.services.price_tracker import update_price
from app.services.market_data import (
    fetch_realtime_price, fetch_history_prices, search_stock,
    AKShareServiceError, StockNotFoundError,
)

router = APIRouter(prefix="/api/market", tags=["market"])


@router.post("/price")
def manual_price_input(data: PriceInput, db: Session = Depends(get_db)):
    """手动输入价格"""
    stock = db.query(Stock).filter(Stock.id == data.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    trade_date = data.trade_date or date.today()
    result = update_price(
        db, stock, data.close_price, trade_date,
        high_price=data.high_price,
        low_price=data.low_price,
        open_price=data.open_price,
    )

    return {
        "message": "价格更新成功",
        "new_high": result["new_high"],
        "anchor_updated": result["anchor_updated"],
        "base_n_reset": result["base_n_reset"],
        "latest_close": stock.latest_close,
        "anchor_price": stock.anchor_price,
        "base_n": stock.base_n,
    }


@router.post("/fetch/{stock_code}")
def fetch_price(stock_code: str, db: Session = Depends(get_db)):
    """通过AKShare获取实时行情"""
    try:
        data = fetch_realtime_price(stock_code)
    except StockNotFoundError:
        raise HTTPException(status_code=404, detail="未找到该股票代码，请检查后重试")
    except AKShareServiceError:
        return JSONResponse(
            status_code=503,
            content={"detail": "行情服务暂时不可用，请稍后重试或手动输入价格"},
        )

    if not data:
        raise HTTPException(status_code=404, detail="获取行情失败，请检查股票代码")

    stock = db.query(Stock).filter(Stock.code == stock_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="该股票未添加到系统中")

    result = update_price(
        db, stock, data["price"], date.today(),
        high_price=data.get("high"),
        low_price=data.get("low"),
        open_price=data.get("open"),
        volume=data.get("volume"),
    )

    return {
        "message": "行情获取成功",
        "stock_name": data["name"],
        "price": data["price"],
        "new_high": result["new_high"],
        "anchor_updated": result["anchor_updated"],
    }


@router.post("/fetch-history/{stock_code}")
def fetch_history(stock_code: str, start_date: str = "20200101", db: Session = Depends(get_db)):
    """获取历史K线并批量导入"""
    stock = db.query(Stock).filter(Stock.code == stock_code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="该股票未添加到系统中")

    try:
        prices = fetch_history_prices(stock_code, start_date)
    except AKShareServiceError:
        return JSONResponse(
            status_code=503,
            content={"detail": "历史行情服务暂时不可用，请稍后重试"},
        )

    if not prices:
        raise HTTPException(status_code=404, detail="获取历史数据失败")

    count = 0
    for p in prices:
        update_price(
            db, stock, p["close"], p["date"],
            high_price=p.get("high"),
            low_price=p.get("low"),
            open_price=p.get("open"),
            volume=p.get("volume"),
        )
        count += 1

    return {"message": f"成功导入{count}条历史数据", "count": count}


@router.get("/search")
def search(keyword: str):
    """搜索股票"""
    try:
        results = search_stock(keyword)
    except AKShareServiceError:
        return JSONResponse(
            status_code=503,
            content={"detail": "行情服务暂时不可用，请稍后重试"},
        )
    return results
