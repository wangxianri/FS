// 我的资料 / 修改密码
const api = require('../../../utils/api')
const auth = require('../../../utils/auth')
const store = require('../../../utils/store')
const i18n = require('../../../utils/i18n')

function texts() {
  return {
    myProfile: i18n.t('myProfile'),
    changePassword: i18n.t('changePassword'),
    name: i18n.t('name'),
    phoneUser: i18n.t('phoneUser'),
    role: i18n.t('role'),
    oldPassword: i18n.t('oldPassword'),
    newPassword: i18n.t('newPassword'),
    confirmPassword: i18n.t('confirmPassword'),
    loading: i18n.t('loading'),
    confirm: i18n.t('confirm'),
  }
}

Page({
  data: {
    tab: 'profile',
    user: {},
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    submitting: false,
    txt: texts(),
  },

  onLoad(options) {
    this.setData({
      tab: options.tab === 'password' ? 'password' : 'profile',
      user: store.get('userInfo') || {},
    })
  },

  onTab(e) { this.setData({ tab: e.currentTarget.dataset.tab }) },
  onOld(e) { this.setData({ oldPassword: e.detail.value }) },
  onNew(e) { this.setData({ newPassword: e.detail.value }) },
  onConfirm(e) { this.setData({ confirmPassword: e.detail.value }) },

  async onChangePassword() {
    const { oldPassword, newPassword, confirmPassword } = this.data
    if (!oldPassword || !newPassword) return getApp().toast(i18n.t('pleaseEnterPassword'))
    if (newPassword !== confirmPassword) return getApp().toast(i18n.t('passwordNotMatch'))
    this.setData({ submitting: true })
    try {
      await api.post('/change-password', { oldPassword, newPassword }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      auth.logout()
      setTimeout(() => wx.reLaunch({ url: '/pages/auth/login/login' }), 800)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ submitting: false }) }
  },
})
