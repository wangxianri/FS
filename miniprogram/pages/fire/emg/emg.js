// 应急处置卡
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    noData: i18n.t('noData'),
  }
}

Page({
  data: {
    cards: [],
    loading: true,
    txt: texts(),
  },
  onLoad() { this.load() },
  async load() {
    try {
      const cards = await api.get('/emg/cards', {}, { silent: true })
      this.setData({ cards, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
})
