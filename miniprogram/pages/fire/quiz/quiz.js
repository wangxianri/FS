// 抽考
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')
const orgSel = require('../../../utils/org-select')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    name: i18n.t('name'),
    spotPass: i18n.t('spotPass'),
    spotFail: i18n.t('spotFail'),
    submit: i18n.t('submit'),
  }
}

Page({
  data: {
    questions: [],
    answers: {},          // index -> bool
    employeeName: '',
    org: { units: [], blds: [], plcs: [], unitIndex: 0, bldIndex: 0, plcIndex: 0 },
    result: null,
    loading: true,
    txt: texts(),
  },
  onLoad() {
    orgSel.init(this)
    this.load()
  },
  onOrgUnit(e) { orgSel.onUnit(this, { detail: { value: e.detail.index } }) },
  onOrgBld(e) { orgSel.onBld(this, { detail: { value: e.detail.index } }) },
  onOrgPlc(e) { orgSel.onPlc(this, { detail: { value: e.detail.index } }) },
  async load() {
    try {
      const questions = await api.get('/quiz/questions', {}, { silent: true })
      this.setData({ questions, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
  onName(e) { this.setData({ employeeName: e.detail.value }) },
  onAnswer(e) {
    const idx = e.currentTarget.dataset.index
    const val = e.currentTarget.dataset.val === 'true'
    this.setData({ [`answers[${idx}]`]: val })
  },
  async onSubmit() {
    const { questions, answers, employeeName } = this.data
    const list = Object.keys(answers).map((i) => ({ index: Number(i), answer: answers[i] }))
    if (list.length !== questions.length) return getApp().toast(i18n.t('pleaseCompleteAll'))
    const org = orgSel.ids(this)
    try {
      const result = await api.post('/quiz/submit', { employeeName, answers: list, unitId: org.unitId, buildingId: org.buildingId, placeId: org.placeId }, { silent: true })
      result.detail = result.detail.map((d) => ({ ...d, q: questions[d.index].q }))
      this.setData({ result })
    } catch (e) {}
  },
})
