// auth.js - 认证辅助：登录、微信一键登录、登出、登录态校验
const api = require('./api')
const store = require('./store')

function saveSession(data) {
  store.set('accessToken', data.accessToken)
  store.set('refreshToken', data.refreshToken)
  store.set('userInfo', data.user)
  store.set('phone', data.user.phone)
  const app = getApp()
  if (app) app.globalData.userInfo = data.user
}

// 手机号+密码登录
function login(phone, password) {
  return api.post('/login', { phone, password }, { silent: true }).then((data) => {
    saveSession(data)
    return data.user
  })
}

// 注册
function register(params) {
  return api.post('/register', params, { silent: true }).then((data) => {
    saveSession(data)
    return data.user
  })
}

// 发送验证码
function sendSms(phone, purpose) {
  return api.post('/sms/send', { phone, purpose }, { silent: true })
}

// 微信一键登录
function wxLogin() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(res) {
        if (!res.code) return reject(new Error('微信登录失败'))
        api.post('/wx/login', { code: res.code }, { silent: true }).then((data) => {
          if (data && data.needBind) {
            // 未绑定 -> 进入绑定页
            resolve({ needBind: true, openid: data.openid, unionid: data.unionid })
          } else {
            saveSession(data)
            resolve({ needBind: false, user: data.user })
          }
        }).catch(reject)
      },
      fail: reject,
    })
  })
}

// 微信绑定
function wxBind(params) {
  return api.post('/wx/bind', params, { silent: true }).then((data) => {
    saveSession(data)
    return data.user
  })
}

// 登出
function logout() {
  const token = store.get('accessToken')
  if (token) {
    api.post('/logout', {}, { silent: true }).catch(() => {})
  }
  store.clear()
  const app = getApp()
  if (app) app.globalData.userInfo = null
}

// 确保登录态有效（启动时/页面 onShow 校验）
function ensureLogin() {
  if (!store.get('accessToken')) return Promise.reject(new Error('no login'))
  return api.get('/me', {}, { silent: true }).then((me) => {
    store.set('userInfo', me)
    return me
  })
}

// 是否登录
function isLoggedIn() {
  return !!(store.get('accessToken') && store.get('userInfo'))
}

module.exports = { login, register, sendSms, wxLogin, wxBind, logout, ensureLogin, isLoggedIn, saveSession }
