// 检查标准库
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    search: i18n.t('search'),
    noData: i18n.t('noData'),
  }
}

Page({
  data: {
    areaFilters: ['全部', '消防控制室', '机房', '气体灭火区', '蓄电池室', '配电室', '储油设施', '疏散通道', '防火分隔', '灭火器', '消火栓', '防排烟', '应急照明', '动火作业'],
    activeArea: '',
    keyword: '',
    items: [],
    loading: true,
    txt: texts(),
  },

  onLoad() { this.load() },
  onKeyword(e) { this.setData({ keyword: e.detail.value }, () => this.load()) },
  onArea(e) {
    const area = e.currentTarget.dataset.key
    this.setData({ activeArea: area === '全部' ? '' : area }, () => this.load())
  },

  async load() {
    const { activeArea, keyword } = this.data
    try {
      const items = await api.get('/check-items', { area: activeArea, q: keyword }, { silent: true })
      const mapped = items.map((it) => ({
        ...it,
        levelLabel: it.level === 'high' ? i18n.t('levelHigh') : it.level === 'mid' ? i18n.t('levelMid') : i18n.t('levelLow'),
        levelTag: it.level === 'high' ? 'tag-red' : it.level === 'mid' ? 'tag-orange' : 'tag-blue',
      }))
      this.setData({ items: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  goDetail(e) { wx.navigateTo({ url: `/pages/fire/check-item-detail/check-item-detail?id=${e.currentTarget.dataset.id}` }) },
})
