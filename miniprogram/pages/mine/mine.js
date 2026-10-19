// 我的（Tab）
const auth = require('../../utils/auth')
const store = require('../../utils/store')
const i18n = require('../../utils/i18n')

function langKey(lang) {
  const map = { 'zh-CN': 'langZhCn', 'en-US': 'langEnUs', 'zh-TW': 'langZhTw' }
  return map[lang] || 'langZhCn'
}

function texts(lang) {
  return {
    myProfile: i18n.t('myProfile'),
    changePassword: i18n.t('changePassword'),
    adminUsers: i18n.t('adminUsers'),
    language: i18n.t('language'),
    about: i18n.t('about'),
    agreement: i18n.t('agreement'),
    privacyPolicy: i18n.t('privacyPolicy'),
    logout: i18n.t('logout'),
    confirm: i18n.t('confirm'),
    logoutConfirm: i18n.t('logoutConfirm'),
    appName: i18n.t('appName'),
    version: i18n.t('version'),
    langLabel: i18n.t(langKey(lang)),
  }
}

Page({
  data: {
    user: {},
    lang: 'zh-CN',
    txt: texts('zh-CN'),
  },

  onShow() {
    if (!auth.isLoggedIn()) {
      wx.reLaunch({ url: '/pages/auth/login/login' })
      return
    }
    const user = store.get('userInfo') || {}
    const lang = store.get('lang') || 'zh-CN'
    this.setData({ user, lang, txt: texts(lang) })
    if (typeof this.getTabBar === 'function' && this.getTabBar()) this.getTabBar().refresh()
  },

  changeLang() {
    const next = this.data.lang === 'zh-CN' ? 'en-US' : this.data.lang === 'en-US' ? 'zh-TW' : 'zh-CN'
    getApp().setLang(next)
    this.setData({ lang: next, txt: texts(next) })
    getApp().toast(i18n.t(langKey(next)), 'success')
  },
  cap(s) { return s.charAt(0).toUpperCase() + s.slice(1) },

  goProfile() { wx.navigateTo({ url: '/pages/fire/profile/profile' }) },
  goChangePassword() { wx.navigateTo({ url: '/pages/fire/profile/profile?tab=password' }) },
  goAdminUsers() { wx.navigateTo({ url: '/pages/admin/users/users' }) },
  goAgreement() { wx.navigateTo({ url: '/pages/common/agreement/agreement' }) },
  goPrivacy() { wx.navigateTo({ url: '/pages/common/privacy/privacy' }) },
  goAbout() {
    wx.showModal({
      title: i18n.t('appName'),
      content: i18n.t('version') + ' ' + getApp().globalData.version,
      showCancel: false,
    })
  },

  onLogout() {
    wx.showModal({
      title: i18n.t('confirm'),
      content: i18n.t('logoutConfirm'),
      success: (res) => {
        if (res.confirm) {
          auth.logout()
          wx.reLaunch({ url: '/pages/auth/login/login' })
        }
      },
    })
  },
})
