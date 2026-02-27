"""AKShare行情数据集成服务"""

from datetime import date, datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def fetch_realtime_price(stock_code: str) -> Optional[dict]:
    """获取实时行情数据

    Args:
        stock_code: 股票代码，如 "601318"

    Returns:
        {"code": str, "name": str, "price": float, "high": float, "low": float, "open": float, "volume": float}
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == stock_code]
        if row.empty:
            return None
        row = row.iloc[0]
        return {
            "code": str(row["代码"]),
            "name": str(row["名称"]),
            "price": float(row["最新价"]),
            "high": float(row["最高"]),
            "low": float(row["最低"]),
            "open": float(row["今开"]),
            "volume": float(row["成交量"]),
        }
    except Exception as e:
        logger.error(f"获取实时行情失败 {stock_code}: {e}")
        return None


def fetch_history_prices(
    stock_code: str,
    start_date: str = "20200101",
    end_date: Optional[str] = None,
) -> list[dict]:
    """获取历史K线数据

    Args:
        stock_code: 股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        [{"date": date, "close": float, "high": float, "low": float, "open": float, "volume": float}]
    """
    try:
        import akshare as ak
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if df.empty:
            return []
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": datetime.strptime(str(row["日期"]), "%Y-%m-%d").date(),
                "close": float(row["收盘"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["开盘"]),
                "volume": float(row["成交量"]),
            })
        return result
    except Exception as e:
        logger.error(f"获取历史行情失败 {stock_code}: {e}")
        return []


def search_stock(keyword: str) -> list[dict]:
    """搜索股票

    Args:
        keyword: 股票代码或名称关键词

    Returns:
        [{"code": str, "name": str}]
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        mask = df["代码"].str.contains(keyword) | df["名称"].str.contains(keyword)
        matched = df[mask].head(20)
        return [
            {"code": str(row["代码"]), "name": str(row["名称"])}
            for _, row in matched.iterrows()
        ]
    except Exception as e:
        logger.error(f"搜索股票失败 {keyword}: {e}")
        return []
