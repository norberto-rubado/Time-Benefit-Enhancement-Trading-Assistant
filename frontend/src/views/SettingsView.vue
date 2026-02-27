<template>
  <div class="settings-page">
    <h2>系统设置</h2>

    <!-- 策略参数 -->
    <el-card class="settings-card">
      <template #header>策略参数</template>
      <el-form label-width="180px" :model="params">
        <el-form-item label="预期年化收益率 (R)">
          <el-input-number
            v-model="params.R"
            :min="0.01"
            :max="1"
            :step="0.01"
            :precision="2"
          />
          <span class="param-hint">当前: {{ (params.R * 100).toFixed(0) }}%</span>
        </el-form-item>
        <el-form-item label="阶梯幅度 (D)">
          <el-input-number
            v-model="params.D"
            :min="0.01"
            :max="0.5"
            :step="0.005"
            :precision="3"
          />
          <span class="param-hint">当前: {{ (params.D * 100).toFixed(1) }}%</span>
        </el-form-item>
        <el-form-item label="最小持仓天数 (min_N)">
          <el-input-number
            v-model="params.min_N"
            :min="1"
            :max="252"
            :step="1"
          />
          <span class="param-hint">交易日</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveParams" :loading="saving">保存参数</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 股票管理 -->
    <el-card class="settings-card">
      <template #header>
        <div class="card-header-flex">
          <span>股票管理 ({{ stocks.length }}/10)</span>
          <el-button type="primary" size="small" @click="showAddDialog = true" :disabled="stocks.length >= 10">
            <el-icon><Plus /></el-icon> 添加股票
          </el-button>
        </div>
      </template>

      <el-table :data="stocks" stripe>
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" width="120" />
        <el-table-column prop="anchor_price" label="锚点价" width="100">
          <template #default="{ row }">{{ row.anchor_price?.toFixed(2) || '--' }}</template>
        </el-table-column>
        <el-table-column prop="latest_close" label="最新价" width="100">
          <template #default="{ row }">{{ row.latest_close?.toFixed(2) || '--' }}</template>
        </el-table-column>
        <el-table-column prop="base_n" label="理论N" width="80" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/stock/${row.id}`)">详情</el-button>
            <el-popconfirm title="确定删除该股票？所有相关数据将被清除" @confirm="onDelete(row.id)">
              <template #reference>
                <el-button size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 数据管理 -->
    <el-card class="settings-card">
      <template #header>数据管理</template>
      <div class="data-section">
        <div class="data-item">
          <div class="data-info">
            <h4>导出数据</h4>
            <p>将所有股票、仓位、交易记录和设置导出为 JSON 文件，用于备份或迁移。</p>
          </div>
          <el-button type="primary" @click="handleExport" :loading="exporting">
            下载备份
          </el-button>
        </div>
        <el-divider />
        <div class="data-item">
          <div class="data-info">
            <h4>导入数据</h4>
            <p>从 JSON 备份文件恢复数据。注意：导入将替换当前所有数据。</p>
          </div>
          <el-button type="warning" @click="triggerImport" :loading="importing">
            选择文件导入
          </el-button>
          <input
            ref="fileInput"
            type="file"
            accept=".json"
            style="display: none"
            @change="handleImportFile"
          />
        </div>
      </div>
    </el-card>

    <!-- 添加股票对话框 -->
    <el-dialog v-model="showAddDialog" title="添加股票" width="420px">
      <el-form :model="newStock" label-width="80px">
        <el-form-item label="股票代码">
          <el-input v-model="newStock.code" placeholder="如 601318" maxlength="6" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="newStock.name" placeholder="如 中国平安" />
        </el-form-item>
        <el-form-item label="锚点价">
          <el-input-number v-model="newStock.anchor_price" :min="0" :precision="2" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button @click="searchStock" :loading="searching">搜索</el-button>
        </el-form-item>
      </el-form>

      <div v-if="searchResults.length" class="search-results">
        <el-tag
          v-for="r in searchResults"
          :key="r.code"
          class="search-tag"
          @click="selectSearchResult(r)"
          style="cursor: pointer; margin: 4px"
        >
          {{ r.code }} {{ r.name }}
        </el-tag>
      </div>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addStock" :loading="adding">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStockStore } from '../stores/stock'
import { settingsApi, marketApi, dataApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const store = useStockStore()
const stocks = ref([])
const params = ref({ R: 0.28, D: 0.075, min_N: 22 })
const saving = ref(false)
const showAddDialog = ref(false)
const adding = ref(false)
const searching = ref(false)
const searchResults = ref([])
const newStock = ref({ code: '', name: '', anchor_price: null })

// 数据导入导出
const exporting = ref(false)
const importing = ref(false)
const fileInput = ref(null)

async function handleExport() {
  exporting.value = true
  try {
    const { data } = await dataApi.exportData()
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const now = new Date()
    const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
    link.download = `trading_assistant_backup_${timestamp}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('数据导出成功')
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    exporting.value = false
  }
}

function triggerImport() {
  fileInput.value?.click()
}

async function handleImportFile(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // 重置 input 以便再次选择同一文件
  event.target.value = ''

  try {
    await ElMessageBox.confirm(
      '导入将替换当前所有数据，此操作不可撤销。建议先导出备份。是否继续？',
      '确认导入',
      {
        confirmButtonText: '确认导入',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return // 用户取消
  }

  importing.value = true
  try {
    const { data } = await dataApi.importData(file, 'replace')
    const msg = `导入成功！股票: ${data.stats.stocks}, 仓位: ${data.stats.positions}, 交易: ${data.stats.trades}, 价格: ${data.stats.price_history}, 设置: ${data.stats.settings}`
    ElMessage.success(msg)
    // 刷新页面数据
    await loadSettings()
    await loadStocks()
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    importing.value = false
  }
}

async function loadSettings() {
  try {
    const { data } = await settingsApi.get()
    for (const s of data) {
      if (s.key === 'R') params.value.R = parseFloat(s.value)
      else if (s.key === 'D') params.value.D = parseFloat(s.value)
      else if (s.key === 'min_N') params.value.min_N = parseInt(s.value)
    }
  } catch (e) {
    // 使用默认值
  }
}

async function saveParams() {
  saving.value = true
  try {
    await Promise.all([
      settingsApi.update({ key: 'R', value: String(params.value.R) }),
      settingsApi.update({ key: 'D', value: String(params.value.D) }),
      settingsApi.update({ key: 'min_N', value: String(params.value.min_N) }),
    ])
    ElMessage.success('参数保存成功')
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    saving.value = false
  }
}

async function loadStocks() {
  await store.fetchStocks()
  stocks.value = store.stocks
}

async function searchStock() {
  if (!newStock.value.code && !newStock.value.name) return
  searching.value = true
  try {
    const { data } = await marketApi.search(newStock.value.code || newStock.value.name)
    searchResults.value = data
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    searching.value = false
  }
}

function selectSearchResult(r) {
  newStock.value.code = r.code
  newStock.value.name = r.name
  searchResults.value = []
}

async function addStock() {
  if (!newStock.value.code || !newStock.value.name) {
    ElMessage.warning('请填写股票代码和名称')
    return
  }
  adding.value = true
  try {
    await store.createStock(newStock.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    newStock.value = { code: '', name: '', anchor_price: null }
    await loadStocks()
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    adding.value = false
  }
}

async function onDelete(id) {
  try {
    await store.deleteStock(id)
    ElMessage.success('删除成功')
    await loadStocks()
  } catch (e) {
    // 全局拦截器已处理错误提示
  }
}

onMounted(() => {
  loadSettings()
  loadStocks()
})
</script>

<style scoped>
.settings-page h2 {
  font-size: 20px;
  color: #303133;
  margin-bottom: 20px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-hint {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}

.search-results {
  margin-top: 12px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.data-section {
  padding: 0 4px;
}

.data-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.data-info {
  flex: 1;
}

.data-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
}

.data-info p {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}
</style>
