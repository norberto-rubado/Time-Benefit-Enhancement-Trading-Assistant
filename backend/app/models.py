from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.database import Base


class TradeDirection(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class PositionStatus(str, enum.Enum):
    EMPTY = "empty"
    HELD = "held"


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    anchor_price = Column(Float, nullable=True)  # 底仓锚点价(最高收盘价)
    all_time_high = Column(Float, nullable=True)  # 历史最高收盘价
    latest_close = Column(Float, nullable=True)  # 最新收盘价
    base_n = Column(Integer, default=22)  # 底仓理论持仓天数
    high_date = Column(Date, nullable=True)  # 创新高日期
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    positions = relationship("Position", back_populates="stock", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="stock", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="stock", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    trade_date = Column(Date, nullable=False)
    close_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    open_price = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    stock = relationship("Stock", back_populates="price_history")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    slot = Column(Integer, nullable=False)  # 1-4笔
    status = Column(SAEnum(PositionStatus), default=PositionStatus.EMPTY)
    buy_price = Column(Float, nullable=True)  # 实际买入价
    buy_date = Column(Date, nullable=True)  # 买入日期
    shares = Column(Integer, default=0)  # 持仓数量
    holding_days = Column(Integer, default=0)  # 持仓交易日数
    calculated_sell_price = Column(Float, nullable=True)  # 计算的卖出价
    calculated_buy_price = Column(Float, nullable=True)  # 计算的买入价(该笔的预估买入价)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    stock = relationship("Stock", back_populates="positions")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    direction = Column(SAEnum(TradeDirection), nullable=False)
    slot = Column(Integer, nullable=False)  # 对应仓位笔数
    price = Column(Float, nullable=False)
    shares = Column(Integer, nullable=False)
    trade_date = Column(Date, default=date.today)
    note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    stock = relationship("Stock", back_populates="trades")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(String(200), nullable=False)
    description = Column(String(200), nullable=True)
