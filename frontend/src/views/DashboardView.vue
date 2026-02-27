<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h2>投资组合总览</h2>
      <div class="header-stats">
        <el-tag type="info" size="large">持仓股票: {{ dashboard?.total_stocks || 0 }}</el-tag>
        <el-tag type="warning" size="large">持仓笔数: {{ dashboard?.total_held_positions || 0 }}</el-tag>
      </div>
    </div>

    <el-card v-if="!dashboard?.stocks?.length" class="empty-card">
      <el-empty description="暂无股票，请在设置页面添加">
        <el-button type="primary" @click="$router.push('/settings')">去添加</el-button>
      </el-empty>
    </el-card>

    <div v-else class="stock-cards">
      <el-card
        v-for="stock in dashboard.stocks"
        :key="stock.stock_id"
        class="stock-card"
        shadow="hover"
        @click="$router.push(`/stock/${stock.stock_id}`)"
      >
        <template #header>
          <div class="card-header">
            <div class="stock-info">
              <span class="stock-name">{{ stock.stock_name }}</span>
              <span class="stock-code">{{ stock.stock_code }}</span>
            </div>
            <div class="stock-price">
              <span class="price-label">最新价</span>
              <span class="price-value">{{ stock.latest_close?.toFixed(2) || '--' }}</span>
            </div>
          </div>
        </template>

        <div class="card-body">
          <div class="info-row">
            <span class="label">锚点价:</span>
            <span class="value">{{ stock.anchor_price?.toFixed(2) || '--' }}</span>
          </div>
          <div class="info-row">
            <span class="label">理论N:</span>
            <span class="value">{{ stock.base_n }}天</span>
          </div>
          <div class="info-row">
            <span class="label">持仓笔数:</span>
            <span class="value">{{ stock.held_count }}/4</span>
          </div>

          <el-divider />

          <div class="positions-mini">
            <div
              v-for="pos in stock.positions"
              :key="pos.slot"
              class="pos-slot"
              :class="pos.status"
            >
              <span class="slot-num">{{ pos.slot }}</span>
              <span class="slot-status">{{ pos.status === 'held' ? '持仓' : '空' }}</span>
              <span v-if="pos.status === 'held'" class="slot-price">
                {{ pos.buy_price?.toFixed(2) }}
              </span>
              <span v-else class="slot-price">
                {{ (pos.next_buy_price)?.toFixed(2) || '--' }}
              </span>
            </div>
          </div>

          <div v-if="stock.next_action" class="next-action">
            <el-button
              v-if="stock.next_action_slot && stock.next_action_direction"
              :type="stock.next_action.includes('卖') ? 'success' : 'warning'"
              size="small"
              @click="openQuickTrade(stock, $event)"
            >
              {{ stock.next_action }}
            </el-button>
            <el-tag
              v-else
              :type="stock.next_action.includes('卖') ? 'success' : 'warning'"
              size="small"
            >
              {{ stock.next_action }}
            </el-tag>
            <span class="action-price">{{ stock.next_action_price?.toFixed(2) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快捷交易弹窗 -->
    <TradeForm
      v-model:visible="showTradeDialog"
      :stock-id="tradeStockId"
      :stock-name="tradeStockName"
      :slot-num="tradeSlot"
      :direction="tradeDirection"
      :suggested-price="tradeSuggestedPrice"
      @success="onTradeSuccess"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useStockStore } from '../stores/stock'
import { storeToRefs } from 'pinia'
import TradeForm from '../components/TradeForm.vue'

const store = useStockStore()
const { dashboard, loading } = storeToRefs(store)

// 快捷交易弹窗状态
const showTradeDialog = ref(false)
const tradeStockId = ref(null)
const tradeStockName = ref('')
const tradeSlot = ref(1)
const tradeDirection = ref('buy')
const tradeSuggestedPrice = ref(null)

function openQuickTrade(stock, event) {
  event.stopPropagation()  // 阻止卡片导航
  tradeStockId.value = stock.stock_id
  tradeStockName.value = stock.stock_name
  tradeSlot.value = stock.next_action_slot
  tradeDirection.value = stock.next_action_direction
  tradeSuggestedPrice.value = stock.next_action_price
  showTradeDialog.value = true
}

function onTradeSuccess() {
  store.fetchDashboard()
}

onMounted(() => {
  store.fetchDashboard()
})
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h2 {
  font-size: 20px;
  color: #303133;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stock-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.stock-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.stock-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-info {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stock-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stock-code {
  font-size: 13px;
  color: #909399;
}

.stock-price {
  text-align: right;
}

.price-label {
  display: block;
  font-size: 12px;
  color: #909399;
}

.price-value {
  font-size: 18px;
  font-weight: 600;
  color: #e6a23c;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.info-row .label {
  color: #909399;
}

.info-row .value {
  color: #303133;
  font-weight: 500;
}

.positions-mini {
  display: flex;
  gap: 8px;
}

.pos-slot {
  flex: 1;
  text-align: center;
  padding: 8px 4px;
  border-radius: 6px;
  background: #f5f7fa;
  font-size: 12px;
}

.pos-slot.held {
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
}

.pos-slot.empty {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.slot-num {
  display: block;
  font-weight: 600;
  color: #606266;
  margin-bottom: 2px;
}

.slot-status {
  display: block;
  font-size: 11px;
  color: #909399;
}

.slot-price {
  display: block;
  font-size: 12px;
  color: #303133;
  margin-top: 2px;
}

.next-action {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 8px;
}

.action-price {
  font-weight: 600;
  color: #303133;
}

.empty-card {
  max-width: 500px;
  margin: 40px auto;
}
</style>
