// 账号管理（仅 admin）
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    search: i18n.t('search'),
    enabled: i18n.t('enabled'),
    disabled: i18n.t('disabled'),
    noData: i18n.t('noData'),
    createUser: i18n.t('createUser'),
    pleaseEnterPhone: i18n.t('pleaseEnterPhone'),
    pleaseEnterName: i18n.t('pleaseEnterName'),
    role: i18n.t('role'),
    cancel: i18n.t('cancel'),
    save: i18n.t('save'),
  }
}

Page({
  data: {
    users: [],
    roles: [
      { id: 'grass', name: '基层执行' },
      { id: 'mid', name: '中层管理' },
      { id: 'top', name: '领导检查' },
      { id: 'accept', name: '消防验收' },
      { id: 'admin', name: '系统管理员' },
    ],
    keyword: '',
    showCreate: false,
    cPhone: '', cName: '', cRole: 'grass', cRoleName: '基层执行', cPassword: 'Fw12345678',
    loading: true,
    txt: texts(),
  },

  onShow() { this.load() },
  onKeyword(e) { this.setData({ keyword: e.detail.value }, () => this.load()) },

  async load() {
    try {
      const list = await api.get('/admin/users', { q: this.data.keyword }, { silent: true })
      const users = (list || []).map((u) => ({
        ...u,
        roleLabel: fmt.roleName(u.role),
        lastLoginText: fmt.datetime(u.last_login_at),
      }))
      this.setData({ users, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  openCreate() { this.setData({ showCreate: true, cPhone: '', cName: '', cRole: 'grass', cRoleName: '基层执行' }) },
  closeCreate() { this.setData({ showCreate: false }) },
  onCPhone(e) { this.setData({ cPhone: e.detail.value }) },
  onCName(e) { this.setData({ cName: e.detail.value }) },
  onCRole(e) { const r = this.data.roles[e.detail.index]; this.setData({ cRole: r.id, cRoleName: r.name }) },

  async onCreate() {
    const { cPhone, cName, cRole } = this.data
    if (!/^1\d{10}$/.test(cPhone)) return getApp().toast(i18n.t('pleaseEnterPhone'))
    try {
      await api.post('/admin/users', { phone: cPhone, name: cName, role: cRole }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.setData({ showCreate: false })
      this.load()
    } catch (e) {}
  },

  toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    wx.showModal({
      title: i18n.t('confirm'),
      content: status === 1 ? i18n.t('disabled') : i18n.t('enabled'),
      success: async (res) => {
        if (res.confirm) {
          await api.post(`/admin/users/${id}/status`, { status: status === 1 ? 0 : 1 }, { silent: true })
          this.load()
        }
      },
    })
  },

  resetPwd(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: i18n.t('resetPassword'),
      content: 'Fw12345678',
      success: async (res) => {
        if (res.confirm) {
          await api.post(`/admin/users/${id}/reset-password`, { newPassword: 'Fw12345678' }, { silent: true })
          getApp().toast(i18n.t('success'), 'success')
        }
      },
    })
  },

  deleteUser(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: i18n.t('delete'),
      content: i18n.t('confirm'),
      success: async (res) => {
        if (res.confirm) {
          await api.request({ url: `/admin/users/${id}`, method: 'DELETE', silent: true })
          this.load()
        }
      },
    })
  },
})
