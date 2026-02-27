# 时益增效交易助手

基于"野生股神"**时益增效模型**的动态阶梯式网格交易策略 Web 应用。

## 策略简介

时益增效模型是一种结合**复利计算**、**持仓天数**和**阶梯幅度**的量化交易策略，适用于优质个股的分批建仓与止盈管理。

### 核心公式

| 公式 | 说明 |
|------|------|
| `卖出价 = 买入价 × (1 + R/252)^max(N, 22)` | 基于年化收益率的复利止盈 |
| `下一笔买入价 = 卖出价 × (1 - D)` | 阶梯式补仓触发价 |

### 关键参数

| 参数 | 默认值 | 含义 |
|------|--------|------|
| **R** | 0.28 (28%) | 预期年化收益率 |
| **D** | 0.075 (7.5%) | 阶梯下跌幅度 |
| **min_N** | 22 | 最小持仓交易日数 |

### 策略规则

- 每只股票最多 **4 笔**仓位，组合最多 **10 只**股票
- **第 1 笔为底仓，不卖出**；每次创新高时，锚点价更新为最高收盘价
- 第 2-4 笔各自独立计算持仓天数和卖出价
- 阶梯链式传递：第 N+1 笔买入价 = 第 N 笔卖出价 × (1-D)

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI + SQLAlchemy + SQLite |
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 数据源 | 手动输入 + AKShare（A股免费API） |
| 部署 | Docker + docker-compose + Nginx 反向代理 |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   ├── models.py            # ORM 模型 (5张表)
│   │   ├── schemas.py           # Pydantic 模型
│   │   ├── calculator.py        # 核心公式引擎
│   │   ├── routes/              # API 路由
│   │   │   ├── stocks.py        # 股票 CRUD
│   │   │   ├── positions.py     # 仓位管理 + 阶梯计算
│   │   │   ├── trades.py        # 交易记录
│   │   │   ├── market.py        # 行情数据
│   │   │   └── dashboard.py     # 每日汇总
│   │   └── services/            # 业务服务
│   │       ├── market_data.py   # AKShare 集成
│   │       ├── strategy.py      # 策略编排
│   │       └── price_tracker.py # 创新高检测
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/               # 4 个页面
│   │   ├── components/          # 通用组件
│   │   ├── stores/              # Pinia 状态管理
│   │   └── api/                 # Axios API 层
│   ├── package.json
│   └── Dockerfile
├── nginx/nginx.conf
├── docker-compose.yml
└── .env
```

## 快速开始

### Docker 一键部署（推荐）

```bash
git clone https://github.com/norberto-rubado/Time-Benefit-Enhancement-Trading-Assistant.git
cd Time-Benefit-Enhancement-Trading-Assistant
docker-compose up -d --build
```

启动后访问 http://localhost 即可使用。

### 本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器运行在 http://localhost:5173，API 自动代理到后端。

## 功能说明

### 主面板

显示所有股票的汇总信息，包括最新价、锚点价、持仓笔数、阶梯状态和下一步操作建议。

### 股票详情

- 4 笔阶梯可视化（持仓状态、买入价、卖出价、持仓天数、预期收益率）
- 手动输入价格 / AKShare 自动获取行情
- 买入、卖出操作记录

### 交易记录

完整的买卖操作历史，支持按股票筛选和分页。

### 设置

- 策略参数调整（R / D / min_N）
- 股票管理（添加、删除，最多 10 只）
- AKShare 股票搜索

## API 文档

启动后端后访问 http://localhost:8000/docs 查看完整的 Swagger API 文档。

主要端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST/PUT/DELETE | `/api/stocks/` | 股票 CRUD |
| GET | `/api/positions/{stock_id}/ladder` | 获取阶梯计算结果 |
| POST | `/api/positions/{stock_id}/buy` | 记录买入 |
| POST | `/api/positions/{stock_id}/sell` | 记录卖出 |
| POST | `/api/market/price` | 手动输入价格 |
| POST | `/api/market/fetch/{stock_code}` | AKShare 获取行情 |
| GET | `/api/dashboard/summary` | 每日汇总 |

## 数据持久化

SQLite 数据库通过 Docker Volume 持久化，容器重启后数据不会丢失。

## 许可证

MIT
