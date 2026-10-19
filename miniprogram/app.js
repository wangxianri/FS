// app.js - 消防履责助手 独立小程序
const auth = require('./utils/auth')
const store = require('./utils/store')
const i18n = require('./utils/i18n')

App({
  globalData: {
    // API 基础地址：独立后端（复用 EPM 域名 ryza.com.cn，路径前缀 /api/fs 与 EPM 的 /api 隔离）
    // 开发时可指向 http://127.0.0.1:5001/api/fs
    baseUrl: 'https://ryza.com.cn/api/fs',
    // 独立小程序正式 AppId（与 EPM 小程序解耦）
    appId: 'wxe81c9f9794ab7ea8',
    version: '2.0.0',
    lang: 'zh-CN',
    userInfo: null,
  },

  onLaunch() {
    // 读取本地登录态
    const token = store.get('accessToken')
    this.globalData.userInfo = store.get('userInfo') || null
    if (token && !store.get('phone')) {
      // 校验并刷新
      auth.ensureLogin().catch(() => {})
    }
    // 语言
    const lang = store.get('lang') || 'zh-CN'
    this.setLang(lang)
  },

  setLang(lang) {
    this.globalData.lang = lang
    store.set('lang', lang)
    i18n.setLocale(lang)
  },

  t(key, params) {
    return i18n.t(key, params)
  },

  // 全局 Toast（保证 i18n）
  toast(title, icon = 'none') {
    wx.showToast({ title, icon, duration: 2000 })
  },

  // 检查是否登录
  isLoggedIn() {
    return !!(store.get('accessToken') && store.get('userInfo'))
  },

  // 跳转登录
  gotoLogin() {
    wx.navigateTo({ url: '/pages/auth/login/login' })
  },
})
