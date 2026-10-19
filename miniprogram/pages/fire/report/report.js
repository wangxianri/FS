// 工作报告：按日汇总巡检/隐患/台账
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    todayTasks: i18n.t('todayTasks'),
    completed: i18n.t('completed'),
    pending: i18n.t('pending'),
    noData: i18n.t('noData'),
    hazards: i18n.t('hazards'),
    levelHigh: i18n.t('levelHigh'),
    levelMid: i18n.t('levelMid'),
    levelLow: i18n.t('levelLow'),
  }
}

Page({
  data: {
    date: '',
    tasks: [],
    hazards: [],
    loading: true,
    txt: texts(),
  },
  onLoad() {
    this.setData({ date: fmt.now() })
    this.load()
  },
  onDate(e) {
    this.setData({ date: e.detail.value })
    this.load()
  },
  async load() {
    const { date } = this.data
    try {
      const [tasks, hazards] = await Promise.all([
        api.get('/tasks', {}, { silent: true }),
        api.get('/hazards', {}, { silent: true }),
      ])
      const dayTasks = tasks.filter((t) => String(t.due_date || '').slice(0, 10) === date)
      const dayHazards = hazards.filter((h) => String(h.created_at || '').slice(0, 10) === date)
      this.setData({ tasks: dayTasks, hazards: dayHazards, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
})
