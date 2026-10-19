// 微信绑定页（登录绑定已有账号 / 注册新账号并绑定）
const auth = require('../../../utils/auth')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好放进 data）
function texts() {
  return {
    bindWechat: i18n.t('bindWechat'),
    phoneUseTip: i18n.t('phoneUseTip'),
    phoneLogin: i18n.t('phoneLogin'),
    registerAccount: i18n.t('registerAccount'),
    pleaseEnterPhone: i18n.t('pleaseEnterPhone'),
    pleaseEnterPassword: i18n.t('pleaseEnterPassword'),
    pleaseEnterName: i18n.t('pleaseEnterName'),
    pleaseEnterCode: i18n.t('pleaseEnterCode'),
    getCode: i18n.t('getCode'),
    loading: i18n.t('loading'),
    confirm: i18n.t('confirm'),
  }
}

Page({
  data: {
    openid: '', unionid: '',
    mode: 'code',            // code=绑定已有账号, register=注册新账号
    phone: '', password: '', code: '', name: '',
    countdown: 0, loading: false,
    agreed: false,
    txt: texts(),
  },
  onLoad(options) {
    this.setData({
      openid: options.openid || '',
      unionid: options.unionid || '',
    })
  },
  switchMode() {
    this.setData({ mode: this.data.mode === 'code' ? 'register' : 'code' })
  },
  onPhone(e) { this.setData({ phone: e.detail.value }) },
  onPassword(e) { this.setData({ password: e.detail.value }) },
  onCode(e) { this.setData({ code: e.detail.value }) },
  onName(e) { this.setData({ name: e.detail.value }) },

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
      const res = await auth.sendSms(phone, 'bind')
      getApp().toast(i18n.t('sendCodeSuccess'), 'success')
      if (res && res.debug) this.setData({ code: String(res.debug) })
      this.startCountdown()
    } catch (e) {}
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

  async onBind() {
    if (!this.checkAgree()) return
    const { openid, unionid, mode, phone, password, code, name } = this.data
    if (!openid) return getApp().toast(i18n.t('unknownError'))
    this.setData({ loading: true })
    try {
      const params = { openid, unionid, mode, phone }
      if (mode === 'code') {
        params.password = password
        if (!password) return getApp().toast(i18n.t('pleaseEnterPassword'))
      } else {
        params.code = code
        params.name = name
        params.password = password
        if (!code) return getApp().toast(i18n.t('pleaseEnterCode'))
        if (!password) return getApp().toast(i18n.t('pleaseEnterPassword'))
      }
      await auth.wxBind(params)
      getApp().toast(i18n.t('bindSuccess'), 'success')
      setTimeout(() => wx.switchTab({ url: '/pages/fire/home/home' }), 600)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ loading: false }) }
  },
  onUnload() { if (this._timer) clearInterval(this._timer) },
})
