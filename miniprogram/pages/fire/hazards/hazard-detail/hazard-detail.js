// 隐患详情
const api = require('../../../../utils/api')
const fmt = require('../../../../utils/format')
const i18n = require('../../../../utils/i18n')

function safeStatusLabel(status) {
  if (!status) return i18n.t('hazardStatusOpen')
  const s = String(status)
  const key = 'hazardStatus' + (s.charAt(0).toUpperCase() + s.slice(1))
  return i18n.t(key) || status
}

function levelLabel(level) {
  const map = { high: 'levelHigh', mid: 'levelMid', low: 'levelLow' }
  return i18n.t(map[level] || level) || level
}

function texts() {
  return {
    hazardDetail: i18n.t('detail'),
    hazardTitle: i18n.t('hazardTitle'),
    hazardLevel: i18n.t('hazardLevel'),
    hazardDesc: i18n.t('hazardDesc'),
    owner: i18n.t('owner'),
    deadline: i18n.t('deadline'),
    days: i18n.t('days'),
    status: '状态',
    area: '区域',
    createdAt: '创建时间',
    rectify: i18n.t('rectify'),
    recheck: i18n.t('recheck'),
    close: i18n.t('close'),
    reopen: i18n.t('reopen'),
    rectificationNote: i18n.t('rectificationNote'),
    recheckNote: i18n.t('recheckNote'),
    cancel: i18n.t('cancel'),
    save: i18n.t('save'),
    confirm: i18n.t('confirm'),
    submit: i18n.t('submit'),
    loading: i18n.t('loading'),
    notePlaceholder: '请填写说明',
    loadingText: '加载中...',
  }
}

Page({
  data: {
    id: null,
    hazard: {},
    note: '',
    action: '',
    loading: true,
    submitting: false,
    txt: texts(),
  },

  onLoad(options) {
    this.setData({ id: options.id }, () => this.load())
  },

  async load() {
    this.setData({ loading: true })
    try {
      const h = await api.get(`/hazards/${this.data.id}`, {}, { silent: true })
      const hazard = {
        ...h,
        levelLabel: levelLabel(h.level),
        statusLabel: safeStatusLabel(h.status),
        createdAtText: fmt.datetime(h.created_at || h.create_time),
      }
      this.setData({ hazard, loading: false })
    } catch (e) {
      this.setData({ loading: false })
      getApp().toast(i18n.t('networkError'))
    }
  },

  onNote(e) { this.setData({ note: e.detail.value }) },

  openAction(e) {
    const action = e.currentTarget.dataset.action
    this.setData({ action, note: '' })
  },
  closeAction() { this.setData({ action: '' }) },

  async submitAction() {
    const { action, note } = this.data
    if (!action) return
    this.setData({ submitting: true })
    try {
      await api.post(`/hazards/${this.data.id}/${action}`, { note }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.setData({ action: '' })
      this.load()
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ submitting: false }) }
  },

  previewPhoto(e) {
    const idx = e.currentTarget.dataset.index
    const urls = this.data.hazard.photos || []
    if (urls.length) wx.previewImage({ current: urls[idx], urls })
  },
})
