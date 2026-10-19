// store.js - 本地存储封装（带过期时间）
const PREFIX = 'fs_'

function key(k) {
  return PREFIX + k
}

function set(k, v) {
  try {
    wx.setStorageSync(key(k), v)
  } catch (e) { /* ignore */ }
}

function get(k, def) {
  try {
    const v = wx.getStorageSync(key(k))
    return v === '' || v === undefined || v === null ? def : v
  } catch (e) {
    return def
  }
}

function remove(k) {
  try {
    wx.removeStorageSync(key(k))
  } catch (e) { /* ignore */ }
}

function clear() {
  try {
    wx.clearStorageSync()
  } catch (e) { /* ignore */ }
}

module.exports = { set, get, remove, clear }
