from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum


# --- Enums ---
class TradeDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"


class PositionStatus(str, Enum):
    EMPTY = "empty"
    HELD = "held"


# --- Stock Schemas ---
class StockCreate(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, description="股票代码")
    name: str = Field(..., min_length=1, max_length=50, description="股票名称")
    anchor_price: Optional[float] = Field(None, gt=0, description="底仓锚点价")


class StockUpdate(BaseModel):
    name: Optional[str] = None
    anchor_price: Optional[float] = None


class StockResponse(BaseModel):
    id: int
    code: str
    name: str
    anchor_price: Optional[float]
    all_time_high: Optional[float]
    latest_close: Optional[float]
    base_n: int
    high_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Position Schemas ---
class PositionResponse(BaseModel):
    id: int
    stock_id: int
    slot: int
    status: PositionStatus
    buy_price: Optional[float]
    buy_date: Optional[date]
    shares: int
    holding_days: int
    calculated_sell_price: Optional[float]
    calculated_buy_price: Optional[float]

    class Config:
        from_attributes = True


class LadderStep(BaseModel):
    slot: int
    status: str
    buy_price: Optional[float] = None
    sell_price: Optional[float] = None
    next_buy_price: Optional[float] = None
    holding_days: int = 0
    shares: int = 0
    buy_date: Optional[date] = None
    profit_rate: Optional[float] = None


class LadderResponse(BaseModel):
    stock_id: int
    stock_code: str
    stock_name: str
    anchor_price: Optional[float]
    base_n: int
    R: float
    D: float
    latest_close: Optional[float]
    steps: list[LadderStep]


# --- Trade Schemas ---
class TradeCreate(BaseModel):
    price: float = Field(..., gt=0)
    shares: int = Field(..., gt=0)
    trade_date: Optional[date] = None
    note: Optional[str] = None


class TradeResponse(BaseModel):
    id: int
    stock_id: int
    direction: TradeDirection
    slot: int
    price: float
    shares: int
    trade_date: date
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TradeLogResponse(BaseModel):
    id: int
    stock_id: int
    stock_code: str
    stock_name: str
    direction: TradeDirection
    slot: int
    price: float
    shares: int
    trade_date: date
    note: Optional[str]
    created_at: datetime


# --- Price Schemas ---
class PriceInput(BaseModel):
    stock_id: int
    close_price: float = Field(..., gt=0)
    trade_date: Optional[date] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    open_price: Optional[float] = None


# --- Settings Schemas ---
class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str]

    class Config:
        from_attributes = True


# --- Dashboard Schemas ---
class DashboardStockSummary(BaseModel):
    stock_id: int
    stock_code: str
    stock_name: str
    latest_close: Optional[float]
    anchor_price: Optional[float]
    base_n: int
    held_count: int
    positions: list[LadderStep]
    next_action: Optional[str] = None
    next_action_price: Optional[float] = None


class DashboardResponse(BaseModel):
    total_stocks: int
    total_held_positions: int
    stocks: list[DashboardStockSummary]
