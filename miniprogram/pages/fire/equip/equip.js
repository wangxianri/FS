// 设备操作卡
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    standard: i18n.t('standard'),
    operate: i18n.t('operate'),
    forbid: i18n.t('forbid'),
    param: i18n.t('param'),
  }
}

Page({
  data: {
    guides: [],
    expanded: {},
    loading: true,
    txt: texts(),
  },
  onLoad() { this.load() },
  async load() {
    try {
      const guides = await api.get('/equip/guides', {}, { silent: true })
      this.setData({ guides, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
  toggle(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`expanded[${idx}]`]: !this.data.expanded[idx] })
  },
})
