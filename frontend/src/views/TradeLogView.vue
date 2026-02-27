<template>
  <div class="trade-log">
    <div class="page-header">
      <h2>交易记录</h2>
      <div class="header-controls">
        <el-checkbox v-model="includeVoided" @change="onFilterChange">显示已作废记录</el-checkbox>
        <el-select v-model="filterStockId" placeholder="筛选股票" clearable style="width: 200px">
          <el-option
            v-for="s in stocks"
            :key="s.id"
            :label="`${s.name} (${s.code})`"
            :value="s.id"
          />
        </el-select>
      </div>
    </div>

    <el-card>
      <el-table :data="trades" stripe v-loading="loading">
        <el-table-column prop="trade_date" label="日期" width="110" sortable />
        <el-table-column label="股票" width="160">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">{{ row.stock_name }}</span>
            <span class="code-text" :class="{ voided: row.is_voided }">({{ row.stock_code }})</span>
          </template>
        </el-table-column>
        <el-table-column prop="direction" label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small" :class="{ voided: row.is_voided }">
              {{ row.direction === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="slot" label="笔数" width="60">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">{{ row.slot }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">{{ row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="shares" label="数量" width="100">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">{{ row.shares }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.is_voided" type="info" size="small">已作废</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="100">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">{{ row.note }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="170">
          <template #default="{ row }">
            <span :class="{ voided: row.is_voided }">
              {{ new Date(row.created_at).toLocaleString('zh-CN') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_voided"
              link
              type="danger"
              size="small"
              @click="handleVoid(row)"
            >
              作废
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadTrades"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { tradeApi, stockApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const trades = ref([])
const stocks = ref([])
const loading = ref(false)
const filterStockId = ref(null)
const includeVoided = ref(false)
const currentPage = ref(1)
const pageSize = 50
const total = ref(0)

async function loadTrades() {
  loading.value = true
  try {
    const params = {
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
      include_voided: includeVoided.value,
    }
    if (filterStockId.value) {
      params.stock_id = filterStockId.value
    }
    const [tradesRes, countRes] = await Promise.all([
      tradeApi.list(params),
      tradeApi.count({
        ...(filterStockId.value ? { stock_id: filterStockId.value } : {}),
        include_voided: includeVoided.value,
      }),
    ])
    trades.value = tradesRes.data
    total.value = countRes.data.count
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  currentPage.value = 1
  loadTrades()
}

async function handleVoid(row) {
  const directionText = row.direction === 'buy' ? '买入' : '卖出'
  try {
    await ElMessageBox.confirm(
      `确认作废 ${row.stock_name} 第${row.slot}笔 ${directionText} ${row.shares}股 @ ${row.price.toFixed(2)} 的交易记录？\n\n作废后仓位将自动回滚。`,
      '作废确认',
      {
        confirmButtonText: '确认作废',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return // 用户取消
  }

  try {
    await tradeApi.void(row.id)
    ElMessage.success('交易记录已作废，仓位已回滚')
    await loadTrades()
  } catch (e) {
    // 全局拦截器已处理错误提示
  }
}

onMounted(async () => {
  const { data } = await stockApi.list()
  stocks.value = data
  await loadTrades()
})

watch(filterStockId, () => {
  currentPage.value = 1
  loadTrades()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  color: #303133;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.code-text {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.voided {
  text-decoration: line-through;
  color: #c0c4cc !important;
}
</style>
