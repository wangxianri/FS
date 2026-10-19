// 任务下发（中层管理）
const api = require('../../../utils/api')
const store = require('../../../utils/store')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    targetUnit: i18n.t('targetUnit'),
    deadline: i18n.t('deadline'),
    done: i18n.t('done'),
    cancelled: i18n.t('cancelled'),
    delete: i18n.t('delete'),
    noData: i18n.t('noData'),
    newNotice: i18n.t('newNotice'),
    noticeTitle: i18n.t('noticeTitle'),
    noticeContent: i18n.t('noticeContent'),
    cancel: i18n.t('cancel'),
    submit: i18n.t('submit'),
  }
}

Page({
  data: {
    list: [],
    canManage: false,
    showForm: false,
    title: '', content: '', deadline: '',
    units: [{ id: 0, name: '全部单位' }],
    unitIndex: 0,
    loading: true,
    txt: texts(),
  },

  onLoad() { this.loadUnits() },
  onShow() { this.load() },

  async load() {
    try {
      const list = await api.get('/notices', {}, { silent: true })
      const mapped = list.map((n) => ({ ...n, createdAtText: fmt.datetime(n.created_at) }))
      const role = (store.get('userInfo') || {}).role || ''
      this.setData({ list: mapped, canManage: role === 'mid' || role === 'admin', loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  async loadUnits() {
    try {
      const list = await api.get('/org/units', {}, { silent: true })
      this.setData({ units: [{ id: 0, name: i18n.t('allUnits') }].concat(list || []) })
    } catch (e) {}
  },

  openForm() { this.setData({ showForm: true }) },
  closeForm() { this.setData({ showForm: false }) },
  onTitle(e) { this.setData({ title: e.detail.value }) },
  onContent(e) { this.setData({ content: e.detail.value }) },
  onDeadline(e) { this.setData({ deadline: e.detail.value }) },
  onUnit(e) { this.setData({ unitIndex: e.detail.index }) },

  async onSubmit() {
    const { title, content, deadline, units, unitIndex } = this.data
    if (!title || !title.trim()) return getApp().toast(i18n.t('noticeTitle'))
    const unitId = units[unitIndex] ? units[unitIndex].id : 0
    try {
      await api.post('/notices', { title: title.trim(), content, deadline, unitId }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.setData({ showForm: false, title: '', content: '', deadline: '', unitIndex: 0 })
      this.load()
    } catch (e) {}
  },

  async onStatus(e) {
    const { id, status } = e.currentTarget.dataset
    try {
      await api.post(`/notices/${id}/status`, { status }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.load()
    } catch (e) {}
  },

  onDelete(e) {
    const { id, title } = e.currentTarget.dataset
    wx.showModal({
      title: i18n.t('delete'),
      content: title || '',
      confirmColor: '#e63b2e',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/notices/${id}`, {}, { silent: true })
          getApp().toast(i18n.t('success'), 'success')
          this.load()
        } catch (e) {}
      },
    })
  },
})
