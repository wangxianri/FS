// 消防台账
const api = require('../../../utils/api')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')
const orgSel = require('../../../utils/org-select')

function buildTypes() {
  return [
    { key: 'duty', label: '值班记录' },
    { key: 'patrol', label: '防火巡查' },
    { key: 'inspect', label: '防火检查' },
    { key: 'training', label: '消防培训' },
    { key: 'drill', label: '灭火演练' },
    { key: 'maintenance', label: '消防设施维保' },
    { key: 'rectify', label: '隐患整改' },
    { key: 'archive', label: '消防档案' },
  ]
}

function texts() {
  return {
    ledger: i18n.t('ledger'),
    ledgerType: i18n.t('ledgerType'),
    ledgerTitle: i18n.t('ledgerTitle'),
    ledgerContent: i18n.t('ledgerContent'),
    owner: i18n.t('owner'),
    add: i18n.t('add'),
    edit: i18n.t('edit'),
    cancel: i18n.t('cancel'),
    save: i18n.t('save'),
    delete: i18n.t('delete'),
    submit: i18n.t('submit'),
    noData: i18n.t('noData'),
    loading: i18n.t('loading'),
    selectUnit: i18n.t('selectUnit'),
    selectBuilding: i18n.t('selectBuilding'),
    selectPlace: i18n.t('selectPlace'),
    placeholderTitle: '请输入台账标题',
    placeholderContent: '请输入台账内容',
  }
}

Page({
  data: {
    types: buildTypes(),
    activeType: 'duty',
    activeTypeLabel: '值班记录',
    list: [],
    loading: true,
    showSheet: false,
    isEdit: false,
    editId: null,
    org: orgSel.orgData(),
    form: { title: '', content: '' },
    txt: texts(),
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) this.getTabBar().refresh()
    this.loadData()
  },

  // 离开页面时确保弹窗收起、tabBar 恢复，避免卡住无法导航
  onHide() {
    if (this.data.showSheet) this.closeSheet()
  },

  onType(e) {
    const key = e.currentTarget.dataset.key
    const type = this.data.types.find((t) => t.key === key)
    this.setData({ activeType: key, activeTypeLabel: type ? type.label : '' }, () => this.loadData())
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const list = await api.get('/ledger', { type: this.data.activeType }, { silent: true })
      const mapped = (list || []).map((x) => ({ ...x, createdAtText: fmt.datetime(x.created_at || x.create_time) }))
      this.setData({ list: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  showAdd() {
    this.setTabBarHidden(true)
    this.setData({ showSheet: true, isEdit: false, editId: null, form: { title: '', content: '' } })
    orgSel.init(this)
  },
  closeSheet() {
    this.setTabBarHidden(false)
    this.setData({ showSheet: false })
  },

  // 自定义 tabBar 渲染在页面容器之外，z-index 无法覆盖，弹窗时需临时隐藏
  setTabBarHidden(hidden) {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ hidden })
    }
  },

  // 单位 / 楼宇 / 场所 三级联动（复用 org-select，与随手拍页一致）
  onUnit(e) { orgSel.onUnit(this, { detail: { value: e.detail.index } }) },
  onBld(e) { orgSel.onBld(this, { detail: { value: e.detail.index } }) },
  onPlc(e) { orgSel.onPlc(this, { detail: { value: e.detail.index } }) },

  onTitle(e) { this.setData({ 'form.title': e.detail.value }) },
  onContent(e) { this.setData({ 'form.content': e.detail.value }) },

  async submit() {
    const { form, activeType, isEdit, editId } = this.data
    if (!form.title) return getApp().toast(this.data.txt.ledgerTitle)
    const payload = { type: activeType, title: form.title, content: form.content, ...orgSel.ids(this) }
    try {
      if (isEdit) await api.put(`/ledger/${editId}`, payload, { silent: true })
      else await api.post('/ledger', payload, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      this.closeSheet()
      this.loadData()
    } catch (e) {}
  },
})
