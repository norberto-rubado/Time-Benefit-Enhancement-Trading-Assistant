"""数据导入导出路由"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Stock, Position, Trade, PriceHistory, Setting

router = APIRouter(prefix="/api/data", tags=["data"])


def _parse_date(value) -> Optional[date]:
    """安全解析日期字符串"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            # 尝试 ISO 格式: 2024-01-15
            return date.fromisoformat(value[:10])
        except (ValueError, IndexError):
            return None
    return None


def _parse_datetime(value) -> Optional[datetime]:
    """安全解析日期时间字符串"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    return None
    return None


@router.get("/export")
def export_data(db: Session = Depends(get_db)):
    """导出全部数据为 JSON"""
    stocks = db.query(Stock).all()
    positions = db.query(Position).all()
    trades = db.query(Trade).all()
    price_history = db.query(PriceHistory).all()
    settings = db.query(Setting).all()

    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "stocks": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "anchor_price": s.anchor_price,
                "all_time_high": s.all_time_high,
                "latest_close": s.latest_close,
                "base_n": s.base_n,
                "high_date": s.high_date.isoformat() if s.high_date else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in stocks
        ],
        "positions": [
            {
                "id": p.id,
                "stock_id": p.stock_id,
                "slot": p.slot,
                "status": p.status.value if p.status else "empty",
                "buy_price": p.buy_price,
                "buy_date": p.buy_date.isoformat() if p.buy_date else None,
                "shares": p.shares,
                "holding_days": p.holding_days,
                "calculated_sell_price": p.calculated_sell_price,
                "calculated_buy_price": p.calculated_buy_price,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in positions
        ],
        "trades": [
            {
                "id": t.id,
                "stock_id": t.stock_id,
                "direction": t.direction.value if t.direction else None,
                "slot": t.slot,
                "price": t.price,
                "shares": t.shares,
                "trade_date": t.trade_date.isoformat() if t.trade_date else None,
                "note": t.note,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in trades
        ],
        "price_history": [
            {
                "id": ph.id,
                "stock_id": ph.stock_id,
                "trade_date": ph.trade_date.isoformat() if ph.trade_date else None,
                "close_price": ph.close_price,
                "high_price": ph.high_price,
                "low_price": ph.low_price,
                "open_price": ph.open_price,
                "volume": ph.volume,
                "created_at": ph.created_at.isoformat() if ph.created_at else None,
            }
            for ph in price_history
        ],
        "settings": [
            {
                "id": s.id,
                "key": s.key,
                "value": s.value,
                "description": s.description,
            }
            for s in settings
        ],
    }

    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="trading_assistant_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        },
    )


@router.post("/import")
def import_data(
    file: UploadFile = File(...),
    mode: str = Query("replace", regex="^(replace)$"),
    db: Session = Depends(get_db),
):
    """导入 JSON 数据

    mode: replace - 清空现有数据后导入
    """
    import json

    # 读取并解析 JSON
    try:
        content = file.file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 文件")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")

    # 验证基本结构
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="JSON 格式错误：顶层应为对象")

    if "stocks" not in data:
        raise HTTPException(status_code=400, detail="JSON 格式错误：缺少 stocks 字段")

    warnings = []
    stats = {
        "stocks": 0,
        "positions": 0,
        "trades": 0,
        "price_history": 0,
        "settings": 0,
    }

    try:
        if mode == "replace":
            # 按外键顺序清空所有表
            db.query(Trade).delete()
            db.query(PriceHistory).delete()
            db.query(Position).delete()
            db.query(Stock).delete()
            db.query(Setting).delete()
            db.flush()

        # 构建 stock_id 映射 (old_id -> new_id)
        stock_id_map = {}

        # 导入 Stocks
        for s_data in data.get("stocks", []):
            old_id = s_data.get("id")
            stock = Stock(
                code=s_data["code"],
                name=s_data["name"],
                anchor_price=s_data.get("anchor_price"),
                all_time_high=s_data.get("all_time_high"),
                latest_close=s_data.get("latest_close"),
                base_n=s_data.get("base_n", 22),
                high_date=_parse_date(s_data.get("high_date")),
                created_at=_parse_datetime(s_data.get("created_at")) or datetime.now(),
                updated_at=_parse_datetime(s_data.get("updated_at")) or datetime.now(),
            )
            db.add(stock)
            db.flush()  # 获取新 ID
            if old_id is not None:
                stock_id_map[old_id] = stock.id
            stats["stocks"] += 1

        # 导入 Positions
        for p_data in data.get("positions", []):
            old_stock_id = p_data.get("stock_id")
            new_stock_id = stock_id_map.get(old_stock_id)
            if new_stock_id is None:
                warnings.append(f"Position 跳过: stock_id={old_stock_id} 未找到映射")
                continue

            from app.models import PositionStatus as PS
            status_val = p_data.get("status", "empty")
            try:
                status = PS(status_val)
            except ValueError:
                status = PS.EMPTY

            position = Position(
                stock_id=new_stock_id,
                slot=p_data["slot"],
                status=status,
                buy_price=p_data.get("buy_price"),
                buy_date=_parse_date(p_data.get("buy_date")),
                shares=p_data.get("shares", 0),
                holding_days=p_data.get("holding_days", 0),
                calculated_sell_price=p_data.get("calculated_sell_price"),
                calculated_buy_price=p_data.get("calculated_buy_price"),
                created_at=_parse_datetime(p_data.get("created_at")) or datetime.now(),
                updated_at=_parse_datetime(p_data.get("updated_at")) or datetime.now(),
            )
            db.add(position)
            stats["positions"] += 1

        # 导入 Trades
        for t_data in data.get("trades", []):
            old_stock_id = t_data.get("stock_id")
            new_stock_id = stock_id_map.get(old_stock_id)
            if new_stock_id is None:
                warnings.append(f"Trade 跳过: stock_id={old_stock_id} 未找到映射")
                continue

            from app.models import TradeDirection as TD
            direction_val = t_data.get("direction", "buy")
            try:
                direction = TD(direction_val)
            except ValueError:
                direction = TD.BUY

            trade = Trade(
                stock_id=new_stock_id,
                direction=direction,
                slot=t_data["slot"],
                price=t_data["price"],
                shares=t_data["shares"],
                trade_date=_parse_date(t_data.get("trade_date")) or date.today(),
                note=t_data.get("note"),
                created_at=_parse_datetime(t_data.get("created_at")) or datetime.now(),
            )
            db.add(trade)
            stats["trades"] += 1

        # 导入 PriceHistory
        for ph_data in data.get("price_history", []):
            old_stock_id = ph_data.get("stock_id")
            new_stock_id = stock_id_map.get(old_stock_id)
            if new_stock_id is None:
                warnings.append(f"PriceHistory 跳过: stock_id={old_stock_id} 未找到映射")
                continue

            ph = PriceHistory(
                stock_id=new_stock_id,
                trade_date=_parse_date(ph_data.get("trade_date")) or date.today(),
                close_price=ph_data["close_price"],
                high_price=ph_data.get("high_price"),
                low_price=ph_data.get("low_price"),
                open_price=ph_data.get("open_price"),
                volume=ph_data.get("volume"),
                created_at=_parse_datetime(ph_data.get("created_at")) or datetime.now(),
            )
            db.add(ph)
            stats["price_history"] += 1

        # 导入 Settings
        for s_data in data.get("settings", []):
            setting = Setting(
                key=s_data["key"],
                value=s_data["value"],
                description=s_data.get("description"),
            )
            db.add(setting)
            stats["settings"] += 1

        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

    return {
        "message": "导入成功",
        "stats": stats,
        "warnings": warnings,
    }
