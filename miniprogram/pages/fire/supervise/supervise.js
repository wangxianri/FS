// 隐患督办派单
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    assignTo: i18n.t('assignTo'),
    deadline: i18n.t('deadline'),
    noData: i18n.t('noData'),
    supervise: i18n.t('supervise'),
    hazards: i18n.t('hazards'),
    note: i18n.t('note'),
    cancel: i18n.t('cancel'),
    submit: i18n.t('submit'),
  }
}

Page({
  data: {
    list: [],
    openHazards: [],
    showForm: false,
    hazardId: '', assigneeName: '', deadline: '', note: '',
    loading: true,
    txt: texts(),
  },
  onShow() { this.load() },

  async load() {
    try {
      const list = await api.get('/supervise', {}, { silent: true })
      const mapped = (list || []).map((s) => ({
        ...s,
        createdAtText: fmt.datetime(s.created_at),
        statusLabel: fmt.superviseStatus(s.status),
      }))
      this.setData({ list: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  async openForm() {
    try {
      const hazards = await api.get('/hazards', { status: 'open' }, { silent: true })
      this.setData({ showForm: true, openHazards: hazards, hazardId: hazards[0] ? hazards[0].id : '' })
    } catch (e) {}
  },
  closeForm() { this.setData({ showForm: false }) },
  onHazard(e) { this.setData({ hazardId: e.detail.value }) },
  onAssignee(e) { this.setData({ assigneeName: e.detail.value }) },
  onDeadline(e) { this.setData({ deadline: e.detail.value }) },
  onNote(e) { this.setData({ note: e.detail.value }) },

  async onSubmit() {
    const { hazardId, assigneeName, deadline, note } = this.data
    if (!hazardId) return getApp().toast(i18n.t('hazards'))
    try {
      await api.post('/supervise', { hazardId, assigneeName, deadline, note }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.setData({ showForm: false })
      this.load()
    } catch (e) {}
  },
})
