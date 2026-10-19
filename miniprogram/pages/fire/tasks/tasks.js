// 任务列表（Tab）
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

function buildFilters() {
  return [
    { key: '', label: i18n.t('all') },
    { key: 'twohour', label: i18n.t('periodTwoHour') },
    { key: 'shift', label: i18n.t('periodShift') },
    { key: 'daily', label: i18n.t('periodDaily') },
    { key: 'weekly', label: i18n.t('periodWeekly') },
    { key: 'monthly', label: i18n.t('periodMonthly') },
    { key: 'quarterly', label: i18n.t('periodQuarterly') },
    { key: 'halfyear', label: i18n.t('periodHalfYear') },
    { key: 'yearly', label: i18n.t('periodYearly') },
    { key: 'ondemand', label: i18n.t('periodOnDemand') },
  ]
}

function buildStatusFilters() {
  return [
    { key: '', label: i18n.t('all') },
    { key: 'pending', label: i18n.t('pending') },
    { key: 'rectifying', label: i18n.t('rectifying') },
    { key: 'done', label: i18n.t('completed') },
  ]
}

Page({
  data: {
    filters: buildFilters(),
    statusFilters: buildStatusFilters(),
    activePeriod: '',
    activeStatus: '',
    tasks: [],
    loading: true,
    noData: i18n.t('noData'),
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) this.getTabBar().refresh()
    this.loadTasks()
  },

  async loadTasks() {
    const { activePeriod, activeStatus } = this.data
    try {
      const tasks = await api.get('/tasks', { period: activePeriod, status: activeStatus }, { silent: true })
      const mapped = tasks.map((t) => ({
        ...t,
        periodName: fmt.periodName(t.period),
        statusLabel: t.status === 'done' ? i18n.t('completed')
          : t.status === 'rectifying' ? i18n.t('rectifying') : i18n.t('pending'),
        dueText: t.due_date,
      }))
      this.setData({ tasks: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  onPeriod(e) { this.setData({ activePeriod: e.currentTarget.dataset.key }, () => this.loadTasks()) },
  onStatus(e) { this.setData({ activeStatus: e.currentTarget.dataset.key }, () => this.loadTasks()) },
  goTask(e) { wx.navigateTo({ url: `/pages/fire/task-inspect/task-inspect?id=${e.currentTarget.dataset.id}` }) },
  goCreate() { wx.navigateTo({ url: '/pages/fire/task-inspect/task-inspect?new=1' }) },
})
