// 速查手册：法规对照 + 量化标准
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    lawRegulations: i18n.t('lawRegulations'),
    quantRules: i18n.t('quantRules'),
    search: i18n.t('search'),
    penalty: i18n.t('penalty'),
    noData: i18n.t('noData'),
    standard: i18n.t('standard'),
    howToCheck: i18n.t('howToCheck'),
    basis: i18n.t('basis'),
    judge: i18n.t('judge'),
  }
}

Page({
  data: {
    tab: 'law',          // law / quant
    keyword: '',
    laws: [],
    quants: [],
    loading: true,
    txt: texts(),
  },

  onLoad() { this.loadLaw(); this.loadQuant() },

  onTab(e) { this.setData({ tab: e.currentTarget.dataset.tab }) },
  onKeyword(e) { this.setData({ keyword: e.detail.value }, () => this.loadLaw()) },

  async loadLaw() {
    const { keyword } = this.data
    try {
      const laws = await api.get('/reference', { q: keyword }, { silent: true })
      this.setData({ laws, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  async loadQuant() {
    try {
      const quants = await api.get('/quant', {}, { silent: true })
      this.setData({ quants })
    } catch (e) {}
  },
})
