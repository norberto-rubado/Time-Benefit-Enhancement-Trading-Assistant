<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="direction === 'buy' ? `买入第${slotNum}笔` : `卖出第${slotNum}笔`"
    width="420px"
  >
    <el-form :model="form" label-width="80px">
      <el-form-item label="股票">
        <span>{{ stockName }}</span>
      </el-form-item>
      <el-form-item label="方向">
        <el-tag :type="direction === 'buy' ? 'danger' : 'success'">
          {{ direction === 'buy' ? '买入' : '卖出' }}
        </el-tag>
        <span style="margin-left: 8px; color: #909399">第{{ slotNum }}笔</span>
      </el-form-item>
      <el-form-item label="价格" required>
        <el-input-number v-model="form.price" :min="0.01" :precision="2" :step="0.1" style="width: 100%" />
        <div v-if="suggestedPrice" class="suggested">
          建议价格: {{ suggestedPrice.toFixed(2) }}
          <el-button link type="primary" size="small" @click="form.price = suggestedPrice">使用</el-button>
        </div>
      </el-form-item>
      <el-form-item label="数量" required>
        <el-input-number v-model="form.shares" :min="100" :step="100" style="width: 100%" />
        <div class="quick-shares">
          <el-button
            v-for="n in [100, 200, 500, 1000]"
            :key="n"
            size="small"
            :type="form.shares === n ? 'primary' : 'default'"
            @click="form.shares = n"
          >
            {{ n }}股
          </el-button>
        </div>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="form.trade_date" type="date" value-format="YYYY-MM-DD" placeholder="默认今天" style="width: 100%" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.note" placeholder="可选" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button :type="direction === 'buy' ? 'warning' : 'success'" @click="submit" :loading="submitting">
        确认{{ direction === 'buy' ? '买入' : '卖出' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { positionApi } from '../api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  stockId: Number,
  stockName: String,
  slotNum: Number,
  direction: String,
  suggestedPrice: Number,
})

const emit = defineEmits(['update:visible', 'success'])

const form = ref({ price: null, shares: 100, trade_date: null, note: '' })
const submitting = ref(false)

watch(() => props.visible, (val) => {
  if (val) {
    form.value = {
      price: props.suggestedPrice || null,
      shares: 100,
      trade_date: null,
      note: '',
    }
  }
})

async function submit() {
  if (!form.value.price || !form.value.shares) {
    ElMessage.warning('请填写价格和数量')
    return
  }
  submitting.value = true
  try {
    const api = props.direction === 'buy' ? positionApi.buy : positionApi.sell
    await api(props.stockId, props.slotNum, form.value)
    ElMessage.success(`${props.direction === 'buy' ? '买入' : '卖出'}成功`)
    emit('update:visible', false)
    emit('success')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.suggested {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.quick-shares {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
