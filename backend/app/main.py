"""时益增效交易助手 - FastAPI入口"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from app.config import settings
from app.database import engine, Base
from app.models import Setting
from app.database import SessionLocal
from app.routes import stocks, positions, trades, market, dashboard, data

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    # 迁移：添加 Trade 作废相关列
    _migrate_trade_void_columns()
    # 初始化默认设置
    _init_default_settings()
    # 预热上交所交易日历缓存
    try:
        from app.calculator import _get_xshg_calendar
        _get_xshg_calendar()
    except Exception:
        pass
    yield


app = FastAPI(
    title="时益增效交易助手",
    description="基于时益增效模型的动态阶梯式网格交易策略工具",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stocks.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(market.router)
app.include_router(dashboard.router)
app.include_router(data.router)


# 设置路由
from app.schemas import SettingUpdate, SettingResponse


@app.get("/api/settings", response_model=list[SettingResponse])
def get_settings():
    db = SessionLocal()
    try:
        return db.query(Setting).all()
    finally:
        db.close()


@app.put("/api/settings")
def update_settings(data: SettingUpdate):
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == data.key).first()
        if setting:
            setting.value = data.value
        else:
            setting = Setting(key=data.key, value=data.value)
            db.add(setting)
        db.commit()
        return {"message": "设置更新成功"}
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


def _init_default_settings():
    db = SessionLocal()
    try:
        defaults = [
            ("R", str(settings.DEFAULT_R), "预期年化收益率"),
            ("D", str(settings.DEFAULT_D), "阶梯幅度(下跌百分比)"),
            ("min_N", str(settings.DEFAULT_MIN_N), "最小持仓交易日数"),
        ]
        for key, value, desc in defaults:
            existing = db.query(Setting).filter(Setting.key == key).first()
            if not existing:
                db.add(Setting(key=key, value=value, description=desc))
        db.commit()
    finally:
        db.close()


def _migrate_trade_void_columns():
    """安全迁移：为 trades 表添加 is_voided 和 voided_at 列"""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("trades")]

    with engine.connect() as conn:
        if "is_voided" not in columns:
            conn.execute(text(
                "ALTER TABLE trades ADD COLUMN is_voided BOOLEAN NOT NULL DEFAULT 0"
            ))
            logger.info("迁移完成: trades 表添加 is_voided 列")

        if "voided_at" not in columns:
            conn.execute(text(
                "ALTER TABLE trades ADD COLUMN voided_at DATETIME"
            ))
            logger.info("迁移完成: trades 表添加 voided_at 列")

        conn.commit()
