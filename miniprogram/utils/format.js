// format.js - 格式化工具
const PERIOD = {
  twohour: { 'zh-CN': '每2小时', 'en-US': '2-hourly', 'zh-TW': '每2小時' },
  shift: { 'zh-CN': '当班', 'en-US': 'Per shift', 'zh-TW': '當班' },
  daily: { 'zh-CN': '每日', 'en-US': 'Daily', 'zh-TW': '每日' },
  weekly: { 'zh-CN': '每周', 'en-US': 'Weekly', 'zh-TW': '每週' },
  monthly: { 'zh-CN': '每月', 'en-US': 'Monthly', 'zh-TW': '每月' },
  quarterly: { 'zh-CN': '每季', 'en-US': 'Quarterly', 'zh-TW': '每季' },
  halfyear: { 'zh-CN': '每半年', 'en-US': 'Half-yearly', 'zh-TW': '每半年' },
  yearly: { 'zh-CN': '每年', 'en-US': 'Yearly', 'zh-TW': '每年' },
  ondemand: { 'zh-CN': '专项', 'en-US': 'On-demand', 'zh-TW': '專項' },
}
const LEVEL = {
  high: { 'zh-CN': '重大', 'en-US': 'High', 'zh-TW': '重大' },
  mid: { 'zh-CN': '较大', 'en-US': 'Medium', 'zh-TW': '較大' },
  low: { 'zh-CN': '一般', 'en-US': 'Low', 'zh-TW': '一般' },
  normal: { 'zh-CN': '正常', 'en-US': 'Normal', 'zh-TW': '正常' },
}
const HAZARD_STATUS = {
  open: { 'zh-CN': '未整改', 'en-US': 'Open', 'zh-TW': '未整改' },
  rectifying: { 'zh-CN': '整改中', 'en-US': 'Rectifying', 'zh-TW': '整改中' },
  rechecked: { 'zh-CN': '待复查', 'en-US': 'To recheck', 'zh-TW': '待複查' },
  closed: { 'zh-CN': '已闭环', 'en-US': 'Closed', 'zh-TW': '已閉環' },
}
const TASK_STATUS = {
  pending: { 'zh-CN': '待完成', 'en-US': 'Pending', 'zh-TW': '待完成' },
  in_progress: { 'zh-CN': '进行中', 'en-US': 'In progress', 'zh-TW': '進行中' },
  rectifying: { 'zh-CN': '需整改', 'en-US': 'Rectify', 'zh-TW': '需整改' },
  done: { 'zh-CN': '已完成', 'en-US': 'Done', 'zh-TW': '已完成' },
}
const SUPERVISE_STATUS = {
  assigned: { 'zh-CN': '已派单', 'en-US': 'Assigned', 'zh-TW': '已派單' },
  in_progress: { 'zh-CN': '进行中', 'en-US': 'In progress', 'zh-TW': '進行中' },
  done: { 'zh-CN': '已完成', 'en-US': 'Done', 'zh-TW': '已完成' },
}
const NOTICE_STATUS = {
  active: { 'zh-CN': '进行中', 'en-US': 'Active', 'zh-TW': '進行中' },
  done: { 'zh-CN': '已完成', 'en-US': 'Done', 'zh-TW': '已完成' },
  cancelled: { 'zh-CN': '已取消', 'en-US': 'Cancelled', 'zh-TW': '已取消' },
}
const REPAIR_STATUS = {
  open: { 'zh-CN': '已登记', 'en-US': 'Registered', 'zh-TW': '已登記' },
  repairing: { 'zh-CN': '维修中', 'en-US': 'Repairing', 'zh-TW': '維修中' },
  checking: { 'zh-CN': '待验收', 'en-US': 'To check', 'zh-TW': '待驗收' },
  closed: { 'zh-CN': '已闭环', 'en-US': 'Closed', 'zh-TW': '已閉環' },
}
const ROLE = {
  grass: { 'zh-CN': '基层执行', 'en-US': 'Grassroots', 'zh-TW': '基層執行' },
  mid: { 'zh-CN': '中层管理', 'en-US': 'Management', 'zh-TW': '中層管理' },
  top: { 'zh-CN': '领导检查', 'en-US': 'Leadership', 'zh-TW': '領導檢查' },
  accept: { 'zh-CN': '消防验收', 'en-US': 'Acceptance', 'zh-TW': '消防驗收' },
  admin: { 'zh-CN': '系统管理员', 'en-US': 'Admin', 'zh-TW': '系統管理員' },
}
const ACCEPT_RESULT = {
  pass: { 'zh-CN': '合格', 'en-US': 'Pass', 'zh-TW': '合格' },
  fail: { 'zh-CN': '不合格', 'en-US': 'Fail', 'zh-TW': '不合格' },
  pending: { 'zh-CN': '待定', 'en-US': 'Pending', 'zh-TW': '待定' },
}
const SPOT_MODE = {
  ten: { 'zh-CN': '十查', 'en-US': 'Ten checks', 'zh-TW': '十查' },
  deep: { 'zh-CN': '深度检查', 'en-US': 'Deep check', 'zh-TW': '深度檢查' },
}

function lang() {
  const app = getApp()
  return (app && app.globalData.lang) || 'zh-CN'
}

function pick(map, key, def) {
  const l = lang()
  const m = map[key]
  if (!m) return def !== undefined ? def : key
  return m[l] || m['zh-CN']
}

function periodName(p) { return pick(PERIOD, p) }
function levelName(l) { return pick(LEVEL, l) }
function hazardStatus(s) { return pick(HAZARD_STATUS, s) }
function taskStatus(s) { return pick(TASK_STATUS, s) }

function pad(n) { return n < 10 ? '0' + n : '' + n }

function now() {
  const d = new Date()
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
}

function datetime(str) {
  if (!str) return ''
  return String(str).replace('T', ' ').slice(0, 16)
}

function relative(str) {
  if (!str) return ''
  const d = new Date(String(str).replace(' ', 'T'))
  const diff = Date.now() - d.getTime()
  const min = Math.floor(diff / 60000)
  if (min < 1) return '刚刚'
  if (min < 60) return min + ' 分钟前'
  const hr = Math.floor(min / 60)
  if (hr < 24) return hr + ' 小时前'
  const day = Math.floor(hr / 24)
  return day + ' 天前'
}

function superviseStatus(s) { return pick(SUPERVISE_STATUS, s) }
function noticeStatus(s) { return pick(NOTICE_STATUS, s) }
function repairStatus(s) { return pick(REPAIR_STATUS, s) }
function roleName(r) { return pick(ROLE, r) }
function acceptResult(s) { return pick(ACCEPT_RESULT, s) }
function spotMode(s) { return pick(SPOT_MODE, s) }

module.exports = {
  periodName, levelName, hazardStatus, taskStatus,
  superviseStatus, noticeStatus, repairStatus, roleName, acceptResult, spotMode,
  now, datetime, relative,
}
