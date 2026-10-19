// custom-tab-bar/index.js - 自定义底部导航（按角色过滤）
const i18n = require('../utils/i18n')
const store = require('../utils/store')

// 完整 tab 列表（含角色白名单；与 app.json tabBar.list 页面一一对应）
const ALL_TABS = [
  { pagePath: '/pages/fire/home/home', icon: '🏠', key: 'home', roles: ['grass', 'mid', 'top', 'accept', 'admin'] },
  { pagePath: '/pages/fire/tasks/tasks', icon: '📋', key: 'tasks', roles: ['grass', 'admin'] },
  { pagePath: '/pages/fire/hazards/hazards', icon: '⚠️', key: 'hazards', roles: ['grass', 'admin'] },
  { pagePath: '/pages/fire/ledger/ledger', icon: '📒', key: 'ledger', roles: ['grass', 'admin'] },
  { pagePath: '/pages/mine/mine', icon: '👤', key: 'mine', roles: ['grass', 'mid', 'top', 'accept', 'admin'] },
]

Component({
  data: {
    selected: 0,
    list: [],
    hidden: false,
  },
  lifetimes: {
    attached() { this.refresh() },
  },
  pageLifetimes: {
    show() { this.refresh() },
  },
  methods: {
    refresh() {
      const userInfo = store.get('userInfo') || {}
      const role = userInfo.role || 'grass'
      const visible = ALL_TABS.filter((t) => (t.roles || []).indexOf(role) >= 0)
      const pages = getCurrentPages()
      const cur = pages[pages.length - 1]
      const idx = visible.findIndex((t) => cur && cur.route === t.pagePath.replace(/^\//, ''))
      const labels = visible.map((t) => ({ ...t, label: i18n.t(t.key) }))
      this.setData({ selected: idx >= 0 ? idx : 0, list: labels })
    },
    onTap(e) {
      const idx = e.currentTarget.dataset.index
      const item = this.data.list[idx]
      if (item) wx.switchTab({ url: item.pagePath })
    },
  },
})
