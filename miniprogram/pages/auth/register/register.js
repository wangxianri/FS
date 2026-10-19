// 注册页
const auth = require('../../../utils/auth')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    registerAccount: i18n.t('registerAccount'),
    phoneUseTip: i18n.t('phoneUseTip'),
    pleaseEnterPhone: i18n.t('pleaseEnterPhone'),
    pleaseEnterName: i18n.t('pleaseEnterName'),
    pleaseEnterCode: i18n.t('pleaseEnterCode'),
    getCode: i18n.t('getCode'),
    pleaseEnterPassword: i18n.t('pleaseEnterPassword'),
    confirmPassword: i18n.t('confirmPassword'),
    loading: i18n.t('loading'),
    register: i18n.t('register'),
  }
}

Page({
  data: {
    phone: '', name: '', code: '', password: '', confirmPassword: '',
    countdown: 0, loading: false,
    agreed: false,
    txt: texts(),
  },
  onPhone(e) { this.setData({ phone: e.detail.value }) },
  onName(e) { this.setData({ name: e.detail.value }) },
  onCode(e) { this.setData({ code: e.detail.value }) },
  onPassword(e) { this.setData({ password: e.detail.value }) },
  onConfirm(e) { this.setData({ confirmPassword: e.detail.value }) },

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

  async sendCode() {
    if (!this.checkAgree()) return
    const { phone } = this.data
    if (!/^1\d{10}$/.test(phone)) return getApp().toast(i18n.t('pleaseEnterPhone'))
    try {
      const res = await auth.sendSms(phone, 'register')
      getApp().toast(i18n.t('sendCodeSuccess'), 'success')
      if (res && res.debug) {
        this.setData({ code: String(res.debug) })
      }
      this.startCountdown()
    } catch (e) { /* 已提示 */ }
  },
  startCountdown() {
    let n = 60
    this.setData({ countdown: n })
    this._timer = setInterval(() => {
      n -= 1
      if (n <= 0) { clearInterval(this._timer); this.setData({ countdown: 0 }) }
      else this.setData({ countdown: n })
    }, 1000)
  },

  async onRegister() {
    if (!this.checkAgree()) return
    const { phone, name, code, password, confirmPassword } = this.data
    if (!/^1\d{10}$/.test(phone)) return getApp().toast(i18n.t('pleaseEnterPhone'))
    if (!code) return getApp().toast(i18n.t('pleaseEnterCode'))
    if (!password) return getApp().toast(i18n.t('pleaseEnterPassword'))
    if (password !== confirmPassword) return getApp().toast(i18n.t('passwordNotMatch'))
    this.setData({ loading: true })
    try {
      await auth.register({ phone, name, code, password })
      getApp().toast(i18n.t('registerSuccess'), 'success')
      setTimeout(() => wx.switchTab({ url: '/pages/fire/home/home' }), 600)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ loading: false }) }
  },
  onUnload() { if (this._timer) clearInterval(this._timer) },
})
