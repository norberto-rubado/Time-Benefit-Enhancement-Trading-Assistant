import { defineStore } from 'pinia'
import { ref } from 'vue'
import { stockApi, positionApi, dashboardApi } from '../api'

export const useStockStore = defineStore('stock', () => {
  const stocks = ref([])
  const currentStock = ref(null)
  const currentLadder = ref(null)
  const dashboard = ref(null)
  const loading = ref(false)

  async function fetchStocks() {
    loading.value = true
    try {
      const { data } = await stockApi.list()
      stocks.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchStock(id) {
    const { data } = await stockApi.get(id)
    currentStock.value = data
    return data
  }

  async function createStock(stockData) {
    const { data } = await stockApi.create(stockData)
    await fetchStocks()
    return data
  }

  async function updateStock(id, stockData) {
    const { data } = await stockApi.update(id, stockData)
    await fetchStocks()
    return data
  }

  async function deleteStock(id) {
    await stockApi.delete(id)
    await fetchStocks()
  }

  async function fetchLadder(stockId) {
    const { data } = await positionApi.getLadder(stockId)
    currentLadder.value = data
    return data
  }

  async function fetchDashboard() {
    loading.value = true
    try {
      const { data } = await dashboardApi.summary()
      dashboard.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return {
    stocks,
    currentStock,
    currentLadder,
    dashboard,
    loading,
    fetchStocks,
    fetchStock,
    createStock,
    updateStock,
    deleteStock,
    fetchLadder,
    fetchDashboard,
  }
})
