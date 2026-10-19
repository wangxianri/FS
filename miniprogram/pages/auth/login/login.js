// 登录页
const auth = require('../../../utils/auth')
const store = require('../../../utils/store')
const i18n = require('../../../utils/i18n')

function texts() {
  return {
    appName: i18n.t('appName'),
    appSlogan: i18n.t('appSlogan'),
    phoneUseTip: i18n.t('phoneUseTip'),
    phoneLabel: i18n.t('phoneLabel'),
    passwordLabel: i18n.t('passwordLabel'),
    pleaseEnterPhone: i18n.t('pleaseEnterPhone'),
    pleaseEnterPassword: i18n.t('pleaseEnterPassword'),
    login: i18n.t('login'),
    loading: i18n.t('loading'),
    phoneLogin: i18n.t('phoneLogin'),
    wechatLogin: i18n.t('wechatLogin'),
    registerAccount: i18n.t('registerAccount'),
    forgotPassword: i18n.t('forgotPassword'),
  }
}

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false,
    agreed: false,
    txt: texts(),
  },

  onPhone(e) { this.setData({ phone: e.detail.value }) },
  onPassword(e) { this.setData({ password: e.detail.value }) },
  togglePassword() { this.setData({ showPassword: !this.data.showPassword }) },

  // 隐私政策/用户协议
  toggleAgree() { this.setData({ agreed: !this.data.agreed }) },
  goAgreement() { wx.navigateTo({ url: '/pages/common/agreement/agreement' }) },
  goPrivacy() { wx.navigateTo({ url: '/pages/common/privacy/privacy' }) },
  checkAgree() {
    if (!this.data.agreed) {
      getApp().toast('请先阅读并同意《用户协议》和《隐私政策》')
      return false
    }
    return true
  },

  // 手机号登录
  async onLogin() {
    if (!this.checkAgree()) return
    const { phone, password } = this.data
    if (!/^1\d{10}$/.test(phone)) return getApp().toast(i18n.t('pleaseEnterPhone'))
    if (!password) return getApp().toast(i18n.t('pleaseEnterPassword'))
    this.setData({ loading: true })
    try {
      await auth.login(phone, password)
      getApp().toast(i18n.t('loginSuccess'), 'success')
      setTimeout(() => {
        wx.switchTab({ url: '/pages/fire/home/home' })
      }, 600)
    } catch (e) {
      // 错误已由 api 提示
    } finally {
      this.setData({ loading: false })
    }
  },

  // 微信一键登录
  async onWxLogin() {
    if (!this.checkAgree()) return
    this.setData({ loading: true })
    try {
      const res = await auth.wxLogin()
      if (res.needBind) {
        wx.navigateTo({ url: `/pages/auth/wx-bind/wx-bind?openid=${res.openid}&unionid=${res.unionid || ''}` })
      } else {
        getApp().toast(i18n.t('loginSuccess'), 'success')
        setTimeout(() => wx.switchTab({ url: '/pages/fire/home/home' }), 600)
      }
    } catch (e) {
      getApp().toast(e && e.message || i18n.t('unknownError'))
    } finally {
      this.setData({ loading: false })
    }
  },

  goRegister() { wx.navigateTo({ url: '/pages/auth/register/register' }) },
  goForgot() { wx.navigateTo({ url: '/pages/auth/forgot/forgot' }) },
})
