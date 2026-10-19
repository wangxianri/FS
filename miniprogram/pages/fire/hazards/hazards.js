// 隐患列表
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

function buildFilters() {
  return [
    { key: '', label: i18n.t('all') },
    { key: 'high', label: i18n.t('levelHigh') },
    { key: 'mid', label: i18n.t('levelMid') },
    { key: 'low', label: i18n.t('levelLow') },
  ]
}

function buildStatusFilters() {
  return [
    { key: '', label: i18n.t('all') },
    { key: 'open', label: i18n.t('hazardStatusOpen') },
    { key: 'rectifying', label: i18n.t('hazardStatusRectifying') },
    { key: 'rechecked', label: i18n.t('hazardStatusRechecked') },
    { key: 'closed', label: i18n.t('hazardStatusClosed') },
  ]
}

Page({
  data: {
    filters: buildFilters(),
    statusFilters: buildStatusFilters(),
    activeLevel: '',
    activeStatus: '',
    hazards: [],
    loading: true,
    noData: i18n.t('noData'),
    txt: {
      reportHazard: i18n.t('reportHazard'),
    },
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) this.getTabBar().refresh()
    this.loadHazards()
  },

  async loadHazards() {
    const { activeLevel, activeStatus } = this.data
    try {
      const list = await api.get('/hazards', { level: activeLevel, status: activeStatus }, { silent: true })
      const hazards = (list || []).map((h) => ({
        ...h,
        levelLabel: fmt.levelName(h.level),
        statusLabel: fmt.hazardStatus(h.status),
        createdAtText: fmt.datetime(h.created_at || h.create_time),
      }))
      this.setData({ hazards, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  onLevel(e) { this.setData({ activeLevel: e.currentTarget.dataset.key }, () => this.loadHazards()) },
  onStatus(e) { this.setData({ activeStatus: e.currentTarget.dataset.key }, () => this.loadHazards()) },
  goDetail(e) { wx.navigateTo({ url: `/pages/fire/hazards/hazard-detail/hazard-detail?id=${e.currentTarget.dataset.id}` }) },
  goReport() { wx.navigateTo({ url: '/pages/fire/hazard-form/hazard-form' }) },
})
