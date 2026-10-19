// 消防验收
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')
const orgSel = require('../../../utils/org-select')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    resultPass: i18n.t('resultPass'),
    resultFail: i18n.t('resultFail'),
    noData: i18n.t('noData'),
    add: i18n.t('add'),
    acceptance: i18n.t('acceptance'),
    projectName: i18n.t('projectName'),
    acceptPoint: i18n.t('acceptPoint'),
    note: i18n.t('note'),
    cancel: i18n.t('cancel'),
    save: i18n.t('save'),
  }
}

Page({
  data: {
    records: [],
    templates: [],
    showForm: false,
    project: '', result: 'pass', note: '',
    tplName: '', tplPoints: [],
    org: { units: [], blds: [], plcs: [], unitIndex: 0, bldIndex: 0, plcIndex: 0 },
    loading: true,
    txt: texts(),
  },

  onLoad() { this.loadTemplates() },

  onShow() { this.loadRecords() },

  async loadTemplates() {
    try {
      const templates = await api.get('/acceptance/templates', {}, { silent: true })
      this.setData({ templates })
    } catch (e) {}
  },

  async loadRecords() {
    try {
      const list = await api.get('/acceptance', {}, { silent: true })
      const mapped = list.map((r) => ({ ...r, createdAtText: fmt.datetime(r.created_at) }))
      this.setData({ records: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  openForm() {
    this.setData({ showForm: true, project: '', result: 'pass', note: '', tplName: '', tplPoints: [] })
    orgSel.init(this)
  },
  closeForm() { this.setData({ showForm: false }) },
  onProject(e) { this.setData({ project: e.detail.value }) },
  onResult(e) { this.setData({ result: e.currentTarget.dataset.val }) },
  onNote(e) { this.setData({ note: e.detail.value }) },
  onOrgUnit(e) { orgSel.onUnit(this, { detail: { value: e.detail.index } }) },
  onOrgBld(e) { orgSel.onBld(this, { detail: { value: e.detail.index } }) },
  onOrgPlc(e) { orgSel.onPlc(this, { detail: { value: e.detail.index } }) },

  pickTemplate(e) {
    const tpl = this.data.templates[e.detail.index]
    this.setData({ tplName: tpl.name, tplPoints: tpl.points })
  },

  async onSubmit() {
    const { project, result, note } = this.data
    if (!project) return getApp().toast(i18n.t('projectName'))
    const org = orgSel.ids(this)
    try {
      await api.post('/acceptance', { project, result, note, unitId: org.unitId, buildingId: org.buildingId, placeId: org.placeId }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.setData({ showForm: false })
      this.loadRecords()
    } catch (e) {}
  },
})
