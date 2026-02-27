<template>
  <div class="stock-detail" v-if="stock">
    <div class="detail-header">
      <el-page-header @back="$router.push('/')">
        <template #content>
          <span class="stock-title">{{ stock.name }} ({{ stock.code }})</span>
        </template>
      </el-page-header>
      <div class="header-actions">
        <el-button @click="showPriceDialog = true" type="warning">
          <el-icon><Edit /></el-icon> 输入价格
        </el-button>
        <el-button @click="fetchMarketPrice" :loading="fetchingPrice">
          <el-icon><Download /></el-icon> 获取行情
        </el-button>
      </div>
    </div>

    <!-- 股票基本信息 -->
    <el-row :gutter="16" class="info-cards">
      <el-col :span="6">
        <el-statistic title="最新收盘价" :value="stock.latest_close || 0" :precision="2" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="锚点价(最高收盘价)" :value="stock.anchor_price || 0" :precision="2" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="理论持仓天数(N)" :value="stock.base_n" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="创新高日期" :value="stock.high_date || '--'" />
      </el-col>
    </el-row>

    <!-- 阶梯可视化 -->
    <el-card class="ladder-card">
      <template #header>
        <div class="ladder-header">
          <span>阶梯仓位</span>
          <div class="ladder-params" v-if="ladder">
            <el-tag size="small">R={{ ladder.R }}</el-tag>
            <el-tag size="small" type="warning">D={{ ladder.D }}</el-tag>
          </div>
        </div>
      </template>
      <PositionLadder
        v-if="ladder"
        :steps="ladder.steps"
        :latest-close="stock.latest_close"
        @buy="onBuy"
        @sell="onSell"
      />
      <el-empty v-else description="请先输入价格以计算阶梯" />
    </el-card>

    <!-- 交易记录 -->
    <el-card class="trades-card">
      <template #header>
        <span>最近交易记录</span>
      </template>
      <el-table :data="recentTrades" stripe size="small" v-if="recentTrades.length">
        <el-table-column prop="trade_date" label="日期" width="110" />
        <el-table-column prop="direction" label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.direction === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="slot" label="笔数" width="60" />
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">{{ row.price.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="shares" label="数量" width="80" />
        <el-table-column prop="note" label="备注" />
      </el-table>
      <el-empty v-else description="暂无交易记录" :image-size="60" />
    </el-card>

    <!-- 手动输入价格对话框 -->
    <PriceInput
      v-model:visible="showPriceDialog"
      :stock-id="stock.id"
      :stock-name="stock.name"
      @success="onPriceUpdated"
    />

    <!-- 买卖操作对话框 -->
    <TradeForm
      v-model:visible="showTradeDialog"
      :stock-id="stock.id"
      :stock-name="stock.name"
      :slot-num="tradeSlot"
      :direction="tradeDirection"
      :suggested-price="suggestedPrice"
      @success="onTradeSuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useStockStore } from '../stores/stock'
import { tradeApi, marketApi } from '../api'
import { ElMessage } from 'element-plus'
import PositionLadder from '../components/PositionLadder.vue'
import PriceInput from '../components/PriceInput.vue'
import TradeForm from '../components/TradeForm.vue'

const props = defineProps({ id: String })
const route = useRoute()
const store = useStockStore()

const stock = ref(null)
const ladder = ref(null)
const recentTrades = ref([])
const showPriceDialog = ref(false)
const showTradeDialog = ref(false)
const tradeSlot = ref(1)
const tradeDirection = ref('buy')
const suggestedPrice = ref(0)
const fetchingPrice = ref(false)

async function loadData() {
  const stockId = props.id || route.params.id
  stock.value = await store.fetchStock(stockId)
  try {
    ladder.value = await store.fetchLadder(stockId)
  } catch (e) {
    // 没有价格数据时阶梯为空
  }
  const { data } = await tradeApi.list({ stock_id: stockId, limit: 10 })
  recentTrades.value = data
}

async function fetchMarketPrice() {
  fetchingPrice.value = true
  try {
    const { data } = await marketApi.fetchPrice(stock.value.code)
    ElMessage.success(`获取成功: ${data.stock_name} ${data.price}`)
    if (data.new_high) {
      ElMessage.warning('创新高! 锚点价已更新')
    }
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '获取行情失败')
  } finally {
    fetchingPrice.value = false
  }
}

function onBuy(step) {
  tradeSlot.value = step.slot
  tradeDirection.value = 'buy'
  suggestedPrice.value = step.next_buy_price || step.buy_price || 0
  showTradeDialog.value = true
}

function onSell(step) {
  tradeSlot.value = step.slot
  tradeDirection.value = 'sell'
  suggestedPrice.value = step.sell_price || 0
  showTradeDialog.value = true
}

function onPriceUpdated() {
  loadData()
}

function onTradeSuccess() {
  loadData()
}

onMounted(loadData)
watch(() => route.params.id, loadData)
</script>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stock-title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.info-cards {
  margin-bottom: 20px;
}

.info-cards .el-col {
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.ladder-card {
  margin-bottom: 20px;
}

.ladder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ladder-params {
  display: flex;
  gap: 8px;
}

.trades-card {
  margin-bottom: 20px;
}
</style>
