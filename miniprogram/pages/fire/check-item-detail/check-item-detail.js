// 检查项详情（法规5要素）
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    veto: i18n.t('veto'),
    area: i18n.t('area'),
    howToCheck: i18n.t('howToCheck'),
    standard: i18n.t('standard'),
    basis: i18n.t('basis'),
    penalty: i18n.t('penalty'),
    fixMeasure: i18n.t('fixMeasure'),
  }
}

Page({
  data: {
    item: null,
    txt: texts(),
  },
  onLoad(options) { this.load(options.id) },
  async load(id) {
    try {
      const item = await api.get(`/check-items/${id}`, {}, { silent: true })
      item.levelLabel = item.level === 'high' ? i18n.t('levelHigh') : item.level === 'mid' ? i18n.t('levelMid') : i18n.t('levelLow')
      item.periodLabel = fmt.periodName(item.period)
      this.setData({ item })
    } catch (e) {}
  },
})
