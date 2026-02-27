import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

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
}

// 行情API
export const marketApi = {
  inputPrice: (data) => api.post('/market/price', data),
  fetchPrice: (stockCode) => api.post(`/market/fetch/${stockCode}`),
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

export default api
