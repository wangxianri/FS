// 任务检查提交页
const api = require('../../../utils/api')
const auth = require('../../../utils/auth')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    checkItems: i18n.t('checkItems'),
    veto: i18n.t('veto'),
    pass: i18n.t('pass'),
    fail: i18n.t('fail'),
    note: i18n.t('note'),
    quickReport: i18n.t('quickReport'),
    hazardTitle: i18n.t('hazardTitle'),
    levelHigh: i18n.t('levelHigh'),
    levelMid: i18n.t('levelMid'),
    levelLow: i18n.t('levelLow'),
    hazardDesc: i18n.t('hazardDesc'),
    loading: i18n.t('loading'),
    submitInspect: i18n.t('submitInspect'),
  }
}

Page({
  data: {
    task: null,
    checkItems: [],
    results: {},          // index -> pass/fail
    notes: {},            // index -> note
    hazardTitle: '',
    hazardLevel: 'mid',
    hazardDesc: '',
    loading: true,
    submitting: false,
    txt: texts(),
  },

  onLoad(options) {
    const tid = options.id
    if (tid) {
      this.tid = tid
      this.loadTask(tid)
    } else {
      // 新建专项任务
      this.setData({ task: { id: 0, name: '', area: '' }, loading: false })
    }
  },

  async loadTask(tid) {
    try {
      const task = await api.get(`/tasks/${tid}`, {}, { silent: true })
      const checkItems = (task.checkItems || []).map((it) => ({ ...it, key: 'c' + it.id }))
      const results = {}
      checkItems.forEach((it, idx) => { results[it.key] = '' })
      this.setData({
        task: { ...task, periodName: fmt.periodName(task.period) },
        checkItems,
        results,
        loading: false,
      })
    } catch (e) { this.setData({ loading: false }) }
  },

  onResult(e) {
    const key = e.currentTarget.dataset.key
    const val = e.currentTarget.dataset.val
    this.setData({ [`results.${key}`]: val }, () => {
      const values = Object.values(this.data.results)
      this.setData({ hasFail: values.includes('fail') })
    })
  },
  onNote(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ [`notes.${key}`]: e.detail.value })
  },
  onHazardTitle(e) { this.setData({ hazardTitle: e.detail.value }) },
  onHazardLevel(e) { this.setData({ hazardLevel: e.currentTarget.dataset.level }) },
  onHazardDesc(e) { this.setData({ hazardDesc: e.detail.value }) },

  async onSubmit() {
    if (this.data.submitting) return
    const { checkItems, results, notes, hazardTitle, hazardLevel, hazardDesc, task } = this.data
    // 校验：存在未评判项
    const hasPending = checkItems.some((it) => !results[it.key])
    if (hasPending) return getApp().toast(i18n.t('pleaseCompleteAll'))
    const list = checkItems.map((it) => ({
      name: it.name,
      result: results[it.key],
      note: notes[it.key] || '',
    }))
    const failItems = list.filter((i) => i.result === 'fail')
    // 若存在不合格但未填隐患标题
    if (failItems.length && !hazardTitle) {
      return getApp().toast(i18n.t('pleaseFillHazard'))
    }
    this.setData({ submitting: true })
    try {
      const payload = {
        area: task.area,
        results: list,
        hazardTitle: failItems.length ? hazardTitle : '',
        hazardLevel,
        hazardDesc,
      }
      await api.post(`/tasks/${task.id}/inspect`, payload, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ submitting: false }) }
  },
})
