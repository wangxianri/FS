// 找回密码
const api = require('../../../utils/api')
const auth = require('../../../utils/auth')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    forgotPassword: i18n.t('forgotPassword'),
    phoneUseTip: i18n.t('phoneUseTip'),
    pleaseEnterPhone: i18n.t('pleaseEnterPhone'),
    pleaseEnterCode: i18n.t('pleaseEnterCode'),
    getCode: i18n.t('getCode'),
    newPassword: i18n.t('newPassword'),
    confirmPassword: i18n.t('confirmPassword'),
    loading: i18n.t('loading'),
    confirm: i18n.t('confirm'),
  }
}

Page({
  data: {
    phone: '', code: '', newPassword: '', confirmPassword: '',
    countdown: 0, loading: false,
    agreed: false,
    txt: texts(),
  },
  onPhone(e) { this.setData({ phone: e.detail.value }) },
  onCode(e) { this.setData({ code: e.detail.value }) },
  onNew(e) { this.setData({ newPassword: e.detail.value }) },
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
      const res = await auth.sendSms(phone, 'forgot')
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

  async onSubmit() {
    if (!this.checkAgree()) return
    const { phone, code, newPassword, confirmPassword } = this.data
    if (newPassword !== confirmPassword) return getApp().toast(i18n.t('passwordNotMatch'))
    this.setData({ loading: true })
    try {
      await api.post('/forgot', { phone, code, newPassword }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ loading: false }) }
  },
  onUnload() { if (this._timer) clearInterval(this._timer) },
})
