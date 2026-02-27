<template>
  <div class="trade-log">
    <div class="page-header">
      <h2>交易记录</h2>
      <el-select v-model="filterStockId" placeholder="筛选股票" clearable style="width: 200px">
        <el-option
          v-for="s in stocks"
          :key="s.id"
          :label="`${s.name} (${s.code})`"
          :value="s.id"
        />
      </el-select>
    </div>

    <el-card>
      <el-table :data="trades" stripe v-loading="loading">
        <el-table-column prop="trade_date" label="日期" width="110" sortable />
        <el-table-column label="股票" width="160">
          <template #default="{ row }">
            <span>{{ row.stock_name }}</span>
            <span class="code-text">({{ row.stock_code }})</span>
          </template>
        </el-table-column>
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
        <el-table-column prop="shares" label="数量" width="100" />
        <el-table-column prop="note" label="备注" min-width="120" />
        <el-table-column prop="created_at" label="记录时间" width="170">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
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

const trades = ref([])
const stocks = ref([])
const loading = ref(false)
const filterStockId = ref(null)
const currentPage = ref(1)
const pageSize = 50
const total = ref(0)

async function loadTrades() {
  loading.value = true
  try {
    const params = {
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize,
    }
    if (filterStockId.value) {
      params.stock_id = filterStockId.value
    }
    const [tradesRes, countRes] = await Promise.all([
      tradeApi.list(params),
      tradeApi.count(filterStockId.value ? { stock_id: filterStockId.value } : {}),
    ])
    trades.value = tradesRes.data
    total.value = countRes.data.count
  } finally {
    loading.value = false
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
</style>
