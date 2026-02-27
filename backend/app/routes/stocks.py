"""股票CRUD路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Position
from app.schemas import StockCreate, StockUpdate, StockResponse
from app.config import settings

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/", response_model=list[StockResponse])
def list_stocks(db: Session = Depends(get_db)):
    return db.query(Stock).order_by(Stock.id).all()


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    return stock


@router.post("/", response_model=StockResponse)
def create_stock(data: StockCreate, db: Session = Depends(get_db)):
    count = db.query(Stock).count()
    if count >= settings.MAX_STOCKS:
        raise HTTPException(status_code=400, detail=f"最多只能添加{settings.MAX_STOCKS}只股票")

    existing = db.query(Stock).filter(Stock.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="该股票代码已存在")

    stock = Stock(
        code=data.code,
        name=data.name,
        anchor_price=data.anchor_price,
        all_time_high=data.anchor_price,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)

    # 初始化4个仓位槽
    for slot in range(1, 5):
        pos = Position(stock_id=stock.id, slot=slot)
        db.add(pos)
    db.commit()

    return stock


@router.put("/{stock_id}", response_model=StockResponse)
def update_stock(stock_id: int, data: StockUpdate, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    if data.name is not None:
        stock.name = data.name
    if data.anchor_price is not None:
        stock.anchor_price = data.anchor_price

    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/{stock_id}")
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")

    db.delete(stock)
    db.commit()
    return {"message": "删除成功"}
