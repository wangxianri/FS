// 检查记录（领导快检记录）
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    spotConclusion: i18n.t('spotConclusion'),
    noData: i18n.t('noData'),
  }
}

Page({
  data: {
    list: [],
    expanded: {},
    loading: true,
    txt: texts(),
  },

  onShow() { this.load() },

  async load() {
    try {
      const list = await api.get('/spot/records', {}, { silent: true })
      const mapped = (list || []).map((s) => {
        let items = []
        try { items = typeof s.items === 'string' ? JSON.parse(s.items) : (s.items || []) } catch (e) { items = [] }
        return {
          ...s,
          items,
          createdAtText: fmt.datetime(s.created_at),
          modeName: s.mode === 'deep' ? i18n.t('deepMode') : i18n.t('tenMode'),
        }
      })
      this.setData({ list: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  toggle(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`expanded[${idx}]`]: !this.data.expanded[idx] })
  },
})
