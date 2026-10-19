// 单位/楼宇/场所 三级联动选择（复用逻辑）
// 用法：
//   const orgSel = require('../../../utils/org-select')
//   data 中新增: org: { units: [], blds: [], plcs: [], unitIndex: 0, bldIndex: 0, plcIndex: 0 }
//   onLoad 调用: orgSel.init(this)
//   wxml 中使用 orgSel.pickerTemplate(this) 生成三个 picker，或手写 picker 绑定 this.data.org
const api = require('./api')

const PLACEHOLDER_UNIT = '请选择所属单位'
const PLACEHOLDER_BLD = '请选择所属楼宇'
const PLACEHOLDER_PLC = '请选择所属场所'

function orgData() {
  return { units: [], blds: [], plcs: [], unitIndex: 0, bldIndex: 0, plcIndex: 0 }
}

function unitLabel(org) {
  return org.unitIndex && org.units[org.unitIndex] ? org.units[org.unitIndex].name : PLACEHOLDER_UNIT
}
function bldLabel(org) {
  return org.bldIndex && org.blds[org.bldIndex] ? org.blds[org.bldIndex].name : PLACEHOLDER_BLD
}
function plcLabel(org) {
  return org.plcIndex && org.plcs[org.plcIndex] ? org.plcs[org.plcIndex].name : PLACEHOLDER_PLC
}

async function init(page) {
  page.setData({ org: orgData() })
  try {
    const list = await api.get('/org/units')
    page.setData({ 'org.units': [{ id: 0, name: PLACEHOLDER_UNIT }].concat(list || []) })
  } catch (e) {}
}

async function onUnit(page, e) {
  const unitIndex = Number(e.detail.value)
  const units = page.data.org.units
  const uid = units[unitIndex] ? units[unitIndex].id : 0
  page.setData({ 'org.unitIndex': unitIndex, 'org.blds': [], 'org.plcs': [], 'org.bldIndex': 0, 'org.plcIndex': 0 })
  if (!uid) return
  try {
    const list = await api.get('/org/buildings?unitId=' + uid)
    page.setData({ 'org.blds': [{ id: 0, name: PLACEHOLDER_BLD }].concat(list || []) })
  } catch (e) {}
}

async function onBld(page, e) {
  const bldIndex = Number(e.detail.value)
  const blds = page.data.org.blds
  const bid = blds[bldIndex] ? blds[bldIndex].id : 0
  page.setData({ 'org.bldIndex': bldIndex, 'org.plcs': [], 'org.plcIndex': 0 })
  if (!bid) return
  const uid = (page.data.org.units[page.data.org.unitIndex] || {}).id || 0
  try {
    const list = await api.get('/org/places?unitId=' + uid + '&buildingId=' + bid)
    page.setData({ 'org.plcs': [{ id: 0, name: PLACEHOLDER_PLC }].concat(list || []) })
  } catch (e) {}
}

function onPlc(page, e) {
  page.setData({ 'org.plcIndex': Number(e.detail.value) })
}

function ids(page) {
  const org = page.data.org || {}
  const u = org.units[org.unitIndex] || {}
  const b = org.blds[org.bldIndex] || {}
  const p = org.plcs[org.plcIndex] || {}
  return { unitId: u.id || 0, buildingId: b.id || 0, placeId: p.id || 0 }
}

module.exports = { orgData, init, onUnit, onBld, onPlc, ids, unitLabel, bldLabel, plcLabel }
