"""
时益增效模型 - 核心计算引擎
纯函数，无IO依赖

核心公式:
- 卖出价 = 买入价 × (1 + R/252)^max(N, min_N)
- 下一笔买入价 = 卖出价 × (1 - D)
- R = 预期年化收益率 (默认0.28)
- D = 阶梯幅度 (默认0.075)
- N = 持仓交易日数
- min_N = 最小持仓天数 (默认22)
"""

from datetime import date, timedelta
from typing import Optional


def calculate_sell_price(buy_price: float, R: float, N: int, min_N: int = 22) -> float:
    """计算卖出价格

    卖出价 = 买入价 × (1 + R/252)^max(N, min_N)
    """
    effective_n = max(N, min_N)
    daily_rate = R / 252
    return buy_price * (1 + daily_rate) ** effective_n


def calculate_next_buy_price(sell_price: float, D: float) -> float:
    """计算下一笔买入价格

    下一笔买入价 = 卖出价 × (1 - D)
    """
    return sell_price * (1 - D)


def calculate_profit_rate(buy_price: float, sell_price: float) -> float:
    """计算收益率"""
    if buy_price <= 0:
        return 0.0
    return (sell_price - buy_price) / buy_price


def count_trading_days(start_date: date, end_date: date) -> int:
    """计算两个日期之间的交易日数（排除周末，简化处理不含节假日）

    从start_date的下一个交易日开始计数到end_date
    """
    if end_date <= start_date:
        return 1

    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 周一到周五
            count += 1
        current += timedelta(days=1)
    return max(count, 1)


def check_new_high(all_time_high: Optional[float], latest_close: float) -> bool:
    """检测是否创新高"""
    if all_time_high is None:
        return True
    return latest_close > all_time_high


def calculate_full_ladder(
    anchor_price: float,
    R: float,
    base_N: int,
    D: float,
    min_N: int,
    held_positions: list[dict],
) -> list[dict]:
    """计算完整4笔阶梯

    Args:
        anchor_price: 底仓锚点价（最高收盘价或初始买入价）
        R: 年化收益率
        base_N: 底仓理论持仓天数
        D: 阶梯幅度
        min_N: 最小持仓天数
        held_positions: 已持仓位列表，每个元素为:
            {
                "slot": int,        # 1-4
                "buy_price": float,  # 实际买入价
                "holding_days": int, # 持仓天数
                "shares": int,      # 持仓数量
                "buy_date": date,   # 买入日期
            }

    Returns:
        4笔阶梯信息列表
    """
    held_map = {p["slot"]: p for p in held_positions}
    steps = []

    # 第1笔（底仓）- 不卖出，锚点价随创新高更新
    slot1_buy_price = anchor_price
    slot1_sell_price = calculate_sell_price(slot1_buy_price, R, base_N, min_N)
    slot1_held = held_map.get(1)

    steps.append({
        "slot": 1,
        "status": "held" if slot1_held else "empty",
        "buy_price": slot1_held["buy_price"] if slot1_held else slot1_buy_price,
        "sell_price": slot1_sell_price,  # 虚拟卖出价，用于计算下一笔
        "next_buy_price": None,  # 底仓不需要
        "holding_days": slot1_held["holding_days"] if slot1_held else base_N,
        "shares": slot1_held["shares"] if slot1_held else 0,
        "buy_date": slot1_held.get("buy_date") if slot1_held else None,
        "profit_rate": None,
        "anchor_price": slot1_buy_price,  # 锚点价（用于显示）
    })

    # 第2-4笔：阶梯链式传递
    prev_sell_price = slot1_sell_price

    for slot in range(2, 5):
        # 该笔的预估买入价 = 上一笔卖出价 × (1-D)
        estimated_buy_price = calculate_next_buy_price(prev_sell_price, D)

        held = held_map.get(slot)

        if held:
            # 已持仓：用实际买入价和持仓天数计算卖出价
            actual_sell_price = calculate_sell_price(
                held["buy_price"], R, held["holding_days"], min_N
            )
            profit_rate = calculate_profit_rate(held["buy_price"], actual_sell_price)

            steps.append({
                "slot": slot,
                "status": "held",
                "buy_price": held["buy_price"],
                "sell_price": actual_sell_price,
                "next_buy_price": calculate_next_buy_price(actual_sell_price, D),
                "holding_days": held["holding_days"],
                "shares": held["shares"],
                "buy_date": held.get("buy_date"),
                "profit_rate": profit_rate,
            })
            # 下一笔的买入价基于该笔的卖出价
            prev_sell_price = actual_sell_price
        else:
            # 未持仓：显示预估买入价和预估卖出价
            estimated_sell_price = calculate_sell_price(
                estimated_buy_price, R, min_N, min_N
            )

            steps.append({
                "slot": slot,
                "status": "empty",
                "buy_price": None,
                "sell_price": estimated_sell_price,
                "next_buy_price": estimated_buy_price,  # 该笔的预估买入价
                "holding_days": 0,
                "shares": 0,
                "buy_date": None,
                "profit_rate": None,
                "estimated_buy_price": estimated_buy_price,
            })
            # 下一笔的买入价基于该笔的预估卖出价
            prev_sell_price = estimated_sell_price

    return steps
