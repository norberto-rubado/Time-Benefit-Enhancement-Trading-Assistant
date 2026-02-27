<template>
  <el-dialog :model-value="visible" @update:model-value="$emit('update:visible', $event)" title="输入价格" width="400px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="股票">
        <span>{{ stockName }}</span>
      </el-form-item>
      <el-form-item label="收盘价" required>
        <el-input-number v-model="form.close_price" :min="0.01" :precision="2" :step="0.1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="form.trade_date" type="date" value-format="YYYY-MM-DD" placeholder="默认今天" style="width: 100%" />
      </el-form-item>
      <el-form-item label="最高价">
        <el-input-number v-model="form.high_price" :min="0" :precision="2" :step="0.1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="最低价">
        <el-input-number v-model="form.low_price" :min="0" :precision="2" :step="0.1" style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="submit" :loading="submitting">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { marketApi } from '../api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: Boolean,
  stockId: Number,
  stockName: String,
})

const emit = defineEmits(['update:visible', 'success'])

const form = ref({
  close_price: null,
  trade_date: null,
  high_price: null,
  low_price: null,
})
const submitting = ref(false)

watch(() => props.visible, (val) => {
  if (val) {
    form.value = { close_price: null, trade_date: null, high_price: null, low_price: null }
  }
})

async function submit() {
  if (!form.value.close_price) {
    ElMessage.warning('请输入收盘价')
    return
  }
  submitting.value = true
  try {
    const { data } = await marketApi.inputPrice({
      stock_id: props.stockId,
      ...form.value,
    })
    let msg = '价格更新成功'
    if (data.new_high) msg += ' (创新高!)'
    ElMessage.success(msg)
    emit('update:visible', false)
    emit('success')
  } catch (e) {
    // 全局拦截器已处理错误提示
  } finally {
    submitting.value = false
  }
}
</script>
