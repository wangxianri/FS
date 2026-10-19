// 首页
const api = require('../../../utils/api')
const auth = require('../../../utils/auth')
const store = require('../../../utils/store')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 模块清单：key -> 页面路由
const MODULES = [
  { key: 'tasks', icon: '📋', nameKey: 'tasks', url: '/pages/fire/tasks/tasks', tab: true, need: ['grass', 'mid', 'admin'] },
  { key: 'hazards', icon: '⚠️', nameKey: 'hazards', url: '/pages/fire/hazards/hazards', tab: true, need: ['grass', 'mid', 'top', 'admin'] },
  { key: 'ledger', icon: '📒', nameKey: 'ledger', url: '/pages/fire/ledger/ledger', tab: true, need: ['grass', 'mid', 'admin'] },
  { key: 'acceptance', icon: '✅', nameKey: 'acceptance', url: '/pages/fire/acceptance/acceptance', need: ['accept', 'admin'] },
  { key: 'check-items', icon: '🔍', nameKey: 'checkItems', url: '/pages/fire/check-items/check-items', need: ['grass', 'mid', 'top', 'accept', 'admin'] },
  { key: 'reference', icon: '📖', nameKey: 'reference', url: '/pages/fire/reference/reference', need: ['grass', 'mid', 'top', 'accept', 'admin'] },
  { key: 'photos', icon: '📷', nameKey: 'photos', url: '/pages/fire/photos/photos', need: ['grass', 'mid', 'accept', 'admin'] },
  { key: 'board', icon: '📊', nameKey: 'board', url: '/pages/fire/board/board', need: ['mid', 'top', 'admin'] },
  { key: 'spot', icon: '🧯', nameKey: 'spotCheck', url: '/pages/fire/spot/spot', need: ['top', 'admin'] },
  { key: 'supervise', icon: '📮', nameKey: 'supervise', url: '/pages/fire/supervise/supervise', need: ['mid', 'admin'] },
  { key: 'quiz', icon: '🎯', nameKey: 'quiz', url: '/pages/fire/quiz/quiz', need: ['mid', 'top', 'admin'] },
  { key: 'emg', icon: '🚨', nameKey: 'emergencyCard', url: '/pages/fire/emg/emg', need: ['grass', 'mid', 'admin'] },
  { key: 'equip', icon: '🛠️', nameKey: 'equipGuide', url: '/pages/fire/equip/equip', need: ['grass', 'mid', 'top', 'admin'] },
  { key: 'report', icon: '📝', nameKey: 'workReport', url: '/pages/fire/report/report', need: ['mid', 'top', 'admin'] },
  { key: 'notice', icon: '📢', nameKey: 'notice', url: '/pages/fire/notice/notice', need: ['mid', 'admin'] },
  { key: 'records', icon: '🗂️', nameKey: 'records', url: '/pages/fire/records/records', need: ['top', 'admin'] },
  { key: 'admin_users', icon: '👥', nameKey: 'adminUsers', url: '/pages/admin/users/users', need: ['admin'] },
]

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    quickActions: i18n.t('quickActions'),
    recentHazards: i18n.t('recentHazards'),
    levelHigh: i18n.t('levelHigh'),
    levelMid: i18n.t('levelMid'),
    levelLow: i18n.t('levelLow'),
  }
}

Page({
  data: {
    user: {},
    today: { date: '', weekday: '' },
    health: { score: 0, status: '', level: '', angle: 0, taskRate: 0 },
    stats: { todayTasks: 0, pendingTasks: 0, openHazards: 0, highHazards: 0, overdue: 0 },
    periodTasks: [],
    tasksToday: [],
    recentHazards: [],
    overdueHazards: [],
    menus: [],
    loading: true,
    refreshing: false,
    txt: texts(),
  },

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/auth/login/login' })
      return
    }
    this.loadHome()
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().refresh()
    }
  },

  async loadHome() {
    try {
      const me = store.get('userInfo')
      let modules = []
      try {
        const meRes = await api.get('/me', {}, { silent: true })
        modules = meRes.modules || []
        store.set('userInfo', meRes)
      } catch (e) {}
      const menus = MODULES.filter((m) => modules.includes(m.key)).map((m) => ({
        ...m, name: i18n.t(m.nameKey),
      }))
      const data = await api.get('/home', {}, { silent: true })
      const recentHazards = (data.recentHazards || []).map((h) => ({
        ...h, createdAtText: fmt.datetime(h.created_at),
      }))
      const health = data.health || {}
      const periodTasks = (data.periodTasks || []).map((g) => ({
        ...g,
        expanded: g.done < g.total, // 有未完成任务默认展开
      }))
      this.setData({
        user: store.get('userInfo') || me,
        today: data.today || { date: '', weekday: '' },
        health: {
          score: health.score || 0,
          status: health.status || '',
          level: health.level || 'poor',
          angle: Math.round(((health.score || 0) / 100) * 360),
          taskRate: health.taskRate || 0,
        },
        stats: data.stats,
        periodTasks,
        tasksToday: data.tasksToday || [],
        recentHazards,
        overdueHazards: data.overdueHazards || [],
        menus,
        loading: false,
        refreshing: false,
      })
    } catch (e) {
      this.setData({ loading: false, refreshing: false })
    }
  },

  // 刷新评分
  refreshHealth() {
    if (this.data.refreshing) return
    this.setData({ refreshing: true })
    this.loadHome()
  },

  // 展开/收起周期分组
  toggleGroup(e) {
    const idx = e.currentTarget.dataset.index
    const key = 'periodTasks[' + idx + '].expanded'
    this.setData({ [key]: !this.data.periodTasks[idx].expanded })
  },

  goTasks() { wx.switchTab({ url: '/pages/fire/tasks/tasks' }) },
  goModule(e) {
    const item = e.currentTarget.dataset.item
    if (!item) return
    if (item.tab) wx.switchTab({ url: item.url })
    else wx.navigateTo({ url: item.url })
  },
  goHazardForm() { wx.navigateTo({ url: '/pages/fire/hazard-form/hazard-form' }) },
  goHazardDetail(e) { wx.navigateTo({ url: `/pages/fire/hazards/hazard-detail/hazard-detail?id=${e.currentTarget.dataset.id}` }) },
  goTask(e) { wx.navigateTo({ url: `/pages/fire/task-inspect/task-inspect?id=${e.currentTarget.dataset.id}` }) },
})
