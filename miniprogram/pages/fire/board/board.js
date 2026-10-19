// 隐患看板
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    all: i18n.t('all'),
    hazardStatusOpen: i18n.t('hazardStatusOpen'),
    hazardStatusRectifying: i18n.t('hazardStatusRectifying'),
    hazardStatusClosed: i18n.t('hazardStatusClosed'),
    levelHigh: i18n.t('levelHigh'),
    levelMid: i18n.t('levelMid'),
    levelLow: i18n.t('levelLow'),
    overdue: i18n.t('overdue'),
    area: i18n.t('area'),
    recentHazards: i18n.t('recentHazards'),
  }
}

Page({
  data: {
    board: null,
    loading: true,
    txt: texts(),
  },
  onShow() { this.load() },
  async load() {
    try {
      const board = await api.get('/hazards/board', {}, { silent: true })
      board.recent = (board.recent || []).map((h) => ({
        ...h,
        statusLabel: i18n.t('hazardStatus' + (h.status.charAt(0).toUpperCase() + h.status.slice(1))),
      }))
      this.setData({ board, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
  goDetail(e) { wx.navigateTo({ url: `/pages/fire/hazards/hazard-detail/hazard-detail?id=${e.currentTarget.dataset.id}` }) },
})
