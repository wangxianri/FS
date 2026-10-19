// 通用可搜索选择器组件
Component({
  properties: {
    // 选项数组，如 [{ id: 1, name: 'xxx' }]
    options: { type: Array, value: [] },
    // 显示字段名
    labelKey: { type: String, value: 'name' },
    // 值字段名
    valueKey: { type: String, value: 'id' },
    // 未选中时的占位文字
    placeholder: { type: String, value: '请选择' },
    // 父组件传入的当前选中项文字
    selectedLabel: { type: String, value: '' },
  },
  data: {
    visible: false,
    keyword: '',
    filtered: [],
  },
  observers: {
    options(options) {
      this.applyFilter(options || [], '')
    },
  },
  methods: {
    open() {
      this.setData({ visible: true, keyword: '' })
      this.applyFilter(this.data.options || [], '')
    },
    close() { this.setData({ visible: false }) },
    prevent() {},
    onSearch(e) {
      this.applyFilter(this.data.options || [], e.detail.value || '')
    },
    applyFilter(options, kw) {
      const labelKey = this.data.labelKey
      const filtered = (options || []).map((o, i) => {
        const isPrimitive = typeof o === 'string' || typeof o === 'number'
        const label = isPrimitive
          ? String(o)
          : (o[labelKey] === undefined || o[labelKey] === null ? '' : String(o[labelKey]))
        return { __index: i, __label: label, __origin: o }
      }).filter((o) => !kw || o.__label.toLowerCase().indexOf(kw.toLowerCase()) >= 0)
      this.setData({ filtered, keyword: kw })
    },
    onSelect(e) {
      const idx = e.currentTarget.dataset.index
      const item = this.data.filtered[idx]
      if (!item) return
      const originIndex = item.__index
      const origin = item.__origin
      const isPrimitive = typeof origin === 'string' || typeof origin === 'number'
      const value = isPrimitive ? origin : origin[this.data.valueKey]
      this.setData({ visible: false })
      this.triggerEvent('change', { item: origin, index: originIndex, value })
    },
  },
})
