// 领导快检：十查/深度
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')
const orgSel = require('../../../utils/org-select')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    spotCheck: i18n.t('spotCheck'),
    deepCheck: i18n.t('deepCheck'),
    spotSite: i18n.t('spotSite'),
    owner: i18n.t('owner'),
    spotPass: i18n.t('spotPass'),
    spotFail: i18n.t('spotFail'),
    veto: i18n.t('veto'),
    loading: i18n.t('loading'),
    submit: i18n.t('submit'),
  }
}

Page({
  data: {
    mode: 'ten',           // ten / deep
    siteName: '',
    items: [],
    passCount: 0, failCount: 0,
    org: { units: [], blds: [], plcs: [], unitIndex: 0, bldIndex: 0, plcIndex: 0 },
    submitting: false,
    txt: texts(),
  },

  onLoad() {
    orgSel.init(this)
    this.loadTemplate()
  },
  onOrgUnit(e) { orgSel.onUnit(this, { detail: { value: e.detail.index } }) },
  onOrgBld(e) { orgSel.onBld(this, { detail: { value: e.detail.index } }) },
  onOrgPlc(e) { orgSel.onPlc(this, { detail: { value: e.detail.index } }) },

  onMode(e) {
    this.setData({ mode: e.currentTarget.dataset.mode }, () => {
      this.loadTemplate()
      this.calc()
    })
  },
  onSiteName(e) { this.setData({ siteName: e.detail.value }) },

  async loadTemplate() {
    try {
      const res = await api.get('/spot/templates', {}, { silent: true })
      const items = res[this.data.mode].map((it) => ({ ...it, pass: false, key: it.name + it.check }))
      this.setData({ items }, () => this.calc())
    } catch (e) {}
  },

  onToggle(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`items[${idx}].pass`]: !this.data.items[idx].pass }, () => this.calc())
  },
  calc() {
    const items = this.data.items
    const pass = items.filter((i) => i.pass).length
    const fail = items.filter((i) => !i.pass).length
    this.setData({ passCount: pass, failCount: fail })
  },

  async onSubmit() {
    const { mode, siteName, items } = this.data
    if (!siteName) return getApp().toast(i18n.t('pleaseEnterSite'))
    const org = orgSel.ids(this)
    this.setData({ submitting: true })
    try {
      const payload = items.map((i) => ({ name: i.name, pass: i.pass, veto: i.veto, check: i.check }))
      await api.post('/spot/check', { mode, siteName, items: payload, unitId: org.unitId, buildingId: org.buildingId, placeId: org.placeId }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {}
    finally { this.setData({ submitting: false }) }
  },
})
