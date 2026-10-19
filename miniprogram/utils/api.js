// api.js - 网络请求封装（Bearer JWT + 401 自动刷新 + 离线拦截）
const store = require('./store')

function baseUrl() {
  const app = getApp()
  return (app && app.globalData.baseUrl) || 'https://ryza.com.cn/api/fs'
}

// 并发刷新防抖
let refreshing = false
let pendingQueue = []

function refreshToken() {
  if (refreshing) {
    return new Promise((resolve, reject) => {
      pendingQueue.push({ resolve, reject })
    })
  }
  refreshing = true
  const refresh = store.get('refreshToken')
  if (!refresh) {
    refreshing = false
    return Promise.reject(new Error('no refresh'))
  }
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseUrl() + '/refresh',
      method: 'POST',
      data: { refreshToken: refresh },
      success(res) {
        if (res.data && res.data.code === 200) {
          const d = res.data.data
          store.set('accessToken', d.accessToken)
          store.set('refreshToken', d.refreshToken)
          store.set('userInfo', d.user)
          resolve(d.accessToken)
        } else {
          // 刷新失败，清登录态
          logoutLocal()
          reject(new Error('refresh fail'))
        }
      },
      fail(err) { reject(err) },
      complete() {
        refreshing = false
        const q = pendingQueue
        pendingQueue = []
        // 失败统一
      },
    })
  })
}

function logoutLocal() {
  store.remove('accessToken')
  store.remove('refreshToken')
  store.remove('userInfo')
  store.remove('phone')
}

// 检查离线模式（积压队列）
function enqueueOffline(op) {
  const queue = store.get('offlineQueue', [])
  queue.push(op)
  store.set('offlineQueue', queue)
}

function offlineFlush() {
  const queue = store.get('offlineQueue', [])
  if (!queue.length) return Promise.resolve({ applied: [], skipped: [] })
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseUrl() + '/offline/sync',
      method: 'POST',
      header: authHeader(),
      data: { ops: queue },
      success(res) {
        if (res.data && res.data.code === 200) {
          store.set('offlineQueue', [])
          resolve(res.data.data)
        } else reject(res)
      },
      fail: reject,
    })
  })
}

function authHeader() {
  const t = store.get('accessToken')
  return t ? { Authorization: 'Bearer ' + t } : {}
}

// 核心请求
function request(options) {
  const { url, method = 'GET', data = {}, silent = false, offline = false } = options
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseUrl() + url,
      method,
      data,
      header: { 'Content-Type': 'application/json', ...authHeader() },
      success(res) {
        const body = res.data || {}
        if (res.statusCode === 401 || body.code === 401) {
          // token 失效 -> 尝试刷新一次
          refreshToken().then((newToken) => {
            wx.request({
              url: baseUrl() + url,
              method,
              data,
              header: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + newToken },
              success(r2) {
                const b2 = r2.data || {}
                if (r2.statusCode === 200 && b2.code === 200) resolve(b2.data)
                else { toLogin(b2); reject(b2) }
              },
              fail: reject,
            })
          }).catch(() => { toLogin(body); reject(body) })
          return
        }
        if (res.statusCode === 200 && body.code === 200) {
          resolve(body.data)
        } else {
          // 业务错误
          if (!silent) {
            wx.showToast({ title: body.message || '请求失败', icon: 'none' })
          }
          reject(body)
        }
      },
      fail(err) {
        // 网络异常：离线模式入队
        if (offline) {
          enqueueOffline({ clientId: (data.clientId) || ('op_' + Date.now()), action: offline, payload: data })
          if (!silent) wx.showToast({ title: '网络异常，已存入离线队列', icon: 'none' })
          resolve({ offline: true })
        } else {
          if (!silent) wx.showToast({ title: '网络连接失败', icon: 'none' })
          reject(err)
        }
      },
    })
  })
}

function toLogin(body) {
  logoutLocal()
  wx.showToast({ title: '登录已过期', icon: 'none' })
  setTimeout(() => {
    wx.navigateTo({ url: '/pages/auth/login/login' })
  }, 500)
}

const api = {
  get: (url, data, opts) => request({ url, method: 'GET', data, ...opts }),
  post: (url, data, opts) => request({ url, method: 'POST', data, ...opts }),
  del: (url, data, opts) => request({ url, method: 'DELETE', data, ...opts }),
  request,
  offlineFlush,
  baseUrl,
}

module.exports = api
