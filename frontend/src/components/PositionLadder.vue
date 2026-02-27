<template>
  <div class="position-ladder">
    <div class="ladder-steps">
      <div
        v-for="step in steps"
        :key="step.slot"
        class="ladder-step"
        :class="[step.status, { 'can-sell': canSell(step), 'can-buy': canBuy(step) }]"
      >
        <div class="step-header">
          <span class="step-slot">第{{ step.slot }}笔</span>
          <el-tag :type="step.status === 'held' ? 'primary' : 'info'" size="small">
            {{ step.slot === 1 ? (step.status === 'held' ? '底仓' : '待建仓') : (step.status === 'held' ? '持仓中' : '空仓') }}
          </el-tag>
        </div>

        <div class="step-body">
          <div class="price-row" v-if="step.status === 'held'">
            <span class="price-label">买入价</span>
            <span class="price-value buy">{{ step.buy_price?.toFixed(2) }}</span>
          </div>
          <div class="price-row" v-if="step.status === 'held' && step.slot > 1">
            <span class="price-label">卖出价</span>
            <span class="price-value sell">{{ step.sell_price?.toFixed(2) }}</span>
          </div>
          <div class="price-row" v-if="step.status === 'held' && step.slot === 1">
            <span class="price-label">虚拟卖出价</span>
            <span class="price-value muted">{{ step.sell_price?.toFixed(2) }}</span>
          </div>
          <div class="price-row" v-if="step.status === 'empty' && step.next_buy_price">
            <span class="price-label">预估买入价</span>
            <span class="price-value buy">{{ step.next_buy_price?.toFixed(2) }}</span>
          </div>

          <div class="info-row" v-if="step.status === 'held'">
            <span>持仓{{ step.holding_days }}天</span>
            <span v-if="step.shares">{{ step.shares }}股</span>
          </div>
          <div class="info-row" v-if="step.status === 'held' && step.profit_rate != null">
            <span>预期收益率</span>
            <span :class="step.profit_rate >= 0 ? 'profit' : 'loss'">
              {{ (step.profit_rate * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="info-row" v-if="step.buy_date">
            <span>买入日期</span>
            <span>{{ step.buy_date }}</span>
          </div>
        </div>

        <div class="step-actions">
          <el-button
            v-if="step.status === 'empty'"
            size="small"
            type="warning"
            @click="$emit('buy', step)"
          >
            买入
          </el-button>
          <el-button
            v-if="step.status === 'held' && step.slot > 1"
            size="small"
            type="success"
            @click="$emit('sell', step)"
          >
            卖出
          </el-button>
          <el-button
            v-if="step.status === 'held' && step.slot === 1"
            size="small"
            type="info"
            disabled
          >
            底仓不卖
          </el-button>
        </div>

        <!-- 连接线 -->
        <div v-if="step.slot < 4" class="connector">
          <div class="connector-line"></div>
          <span class="connector-label">-{{ ((1 - (step.next_buy_price || 0) / (step.sell_price || 1)) * 100).toFixed(1) || 'D' }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, required: true },
  latestClose: { type: Number, default: null },
})

defineEmits(['buy', 'sell'])

function canSell(step) {
  return false // 简化：由用户自行判断
}

function canBuy(step) {
  return false
}
</script>

<style scoped>
.ladder-steps {
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding: 16px 0;
}

.ladder-step {
  flex: 1;
  min-width: 200px;
  padding: 16px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 2px solid #e4e7ed;
  position: relative;
}

.ladder-step.held {
  background: #ecf5ff;
  border-color: #409eff;
}

.ladder-step.empty {
  background: #fafafa;
  border-color: #dcdfe6;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.step-slot {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.step-body {
  margin-bottom: 12px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.price-label {
  font-size: 13px;
  color: #909399;
}

.price-value {
  font-size: 16px;
  font-weight: 600;
}

.price-value.buy {
  color: #e6a23c;
}

.price-value.sell {
  color: #67c23a;
}

.price-value.muted {
  color: #c0c4cc;
  font-size: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
  padding: 2px 0;
}

.profit {
  color: #67c23a;
  font-weight: 500;
}

.loss {
  color: #f56c6c;
  font-weight: 500;
}

.step-actions {
  text-align: center;
}

.connector {
  position: absolute;
  right: -24px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 48px;
}

.connector-line {
  width: 48px;
  height: 2px;
  background: #dcdfe6;
}

.connector-label {
  font-size: 10px;
  color: #c0c4cc;
  margin-top: 2px;
}
</style>
