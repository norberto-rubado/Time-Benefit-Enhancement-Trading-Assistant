import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 全局响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 支持组件自行处理特定请求
    if (error.config?._skipInterceptor) {
      return Promise.reject(error)
    }

    if (!error.response) {
      // 网络错误或超时
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        ElMessage.error('请求超时，请检查网络连接后重试')
      } else {
        ElMessage.error('网络连接失败，请检查网络状态')
      }
    } else {
      const { status, data } = error.response
      if (status === 422) {
        // FastAPI validation error
        const detail = data?.detail
        if (Array.isArray(detail)) {
          const msgs = detail.map((d) => d.msg || d.message || JSON.stringify(d)).join('; ')
          ElMessage.error(`参数错误: ${msgs}`)
        } else {
          ElMessage.error(detail || '请求参数错误')
        }
      } else if (status === 503) {
        ElMessage.warning(data?.detail || '服务暂时不可用，请稍后重试')
      } else if (status === 500) {
        ElMessage.error('服务器内部错误，请稍后重试')
      } else if (status === 502) {
        ElMessage.error('服务暂时不可用，请稍后重试')
      } else if (status >= 400) {
        ElMessage.error(data?.detail || '操作失败')
      }
    }

    return Promise.reject(error)
  }
)

// 股票API
export const stockApi = {
  list: () => api.get('/stocks/'),
  get: (id) => api.get(`/stocks/${id}`),
  create: (data) => api.post('/stocks/', data),
  update: (id, data) => api.put(`/stocks/${id}`, data),
  delete: (id) => api.delete(`/stocks/${id}`),
}

// 仓位API
export const positionApi = {
  getLadder: (stockId) => api.get(`/positions/${stockId}/ladder`),
  buy: (stockId, slot, data) => api.post(`/positions/${stockId}/buy?slot=${slot}`, data),
  sell: (stockId, slot, data) => api.post(`/positions/${stockId}/sell?slot=${slot}`, data),
}

// 交易记录API
export const tradeApi = {
  list: (params) => api.get('/trades/', { params }),
  count: (params) => api.get('/trades/count', { params }),
  void: (tradeId) => api.post(`/trades/${tradeId}/void`),
}

// 行情API
export const marketApi = {
  inputPrice: (data) => api.post('/market/price', data),
  fetchPrice: (stockCode) => api.post(`/market/fetch/${stockCode}`, null, { _skipInterceptor: true }),
  fetchHistory: (stockCode, startDate) => api.post(`/market/fetch-history/${stockCode}?start_date=${startDate || '20200101'}`),
  search: (keyword) => api.get('/market/search', { params: { keyword } }),
}

// 仪表盘API
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
}

// 设置API
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
}

// 数据导入导出API
export const dataApi = {
  exportData: () => api.get('/data/export', { responseType: 'blob' }),
  importData: (file, mode = 'replace') => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/data/import?mode=${mode}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export default api
