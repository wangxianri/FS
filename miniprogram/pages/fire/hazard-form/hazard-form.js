// 上报隐患表单
const api = require('../../../utils/api')
const i18n = require('../../../utils/i18n')

function texts() {
  return {
    pageTitle: i18n.t('reportHazard'),
    hazardTitle: i18n.t('hazardTitle'),
    owner: i18n.t('owner') || '所属单位/楼宇/场所',
    area: i18n.t('area'),
    hazardLevel: i18n.t('hazardLevel'),
    hazardDesc: i18n.t('hazardDesc'),
    deadline: i18n.t('deadline'),
    days: i18n.t('days'),
    photos: i18n.t('photos'),
    submit: i18n.t('submit'),
    loading: i18n.t('loading'),
    levelHigh: i18n.t('levelHigh'),
    levelMid: i18n.t('levelMid'),
    levelLow: i18n.t('levelLow'),
    pleaseEnterTitle: i18n.t('hazardTitle'),
    pleaseEnterArea: i18n.t('area'),
    pleaseEnterDesc: i18n.t('hazardDesc'),
    required: '*',
  }
}

Page({
  data: {
    title: '',
    area: '',
    level: 'mid',
    desc: '',
    days: 3,
    photos: [],
    units: [],
    blds: [],
    plcs: [],
    unitIndex: 0,
    bldIndex: 0,
    plcIndex: 0,
    submitting: false,
    txt: texts(),
  },

  onLoad() {
    this.loadUnits()
  },

  onTitle(e) { this.setData({ title: e.detail.value }) },
  onArea(e) { this.setData({ area: e.detail.value }) },
  onLevel(e) { this.setData({ level: e.currentTarget.dataset.level }) },
  onDesc(e) { this.setData({ desc: e.detail.value }) },
  onDays(e) { this.setData({ days: Number(e.detail.value) || 0 }) },

  // 单位 → 楼宇 → 场所 三级联动
  async loadUnits() {
    try {
      const list = await api.get('/org/units')
      this.setData({ units: [{ id: 0, name: '请选择所属单位' }].concat(list || []) })
    } catch (e) {}
  },
  async onUnit(e) {
    const unitIndex = e.detail.index
    const uid = this.data.units[unitIndex] ? this.data.units[unitIndex].id : 0
    this.setData({ unitIndex, blds: [], plcs: [], bldIndex: 0, plcIndex: 0 })
    if (!uid) return
    try {
      const list = await api.get('/org/buildings?unitId=' + uid)
      this.setData({ blds: [{ id: 0, name: '请选择所属楼宇' }].concat(list || []) })
    } catch (e) {}
  },
  async onBld(e) {
    const bldIndex = e.detail.index
    const bid = this.data.blds[bldIndex] ? this.data.blds[bldIndex].id : 0
    this.setData({ bldIndex, plcs: [], plcIndex: 0 })
    if (!bid) return
    try {
      const list = await api.get('/org/places?unitId=' + (this.data.units[this.data.unitIndex] ? this.data.units[this.data.unitIndex].id : 0) + '&buildingId=' + bid)
      this.setData({ plcs: [{ id: 0, name: '请选择所属场所' }].concat(list || []) })
    } catch (e) {}
  },
  onPlc(e) {
    this.setData({ plcIndex: e.detail.index })
  },
  orgIds() {
    const u = this.data.units[this.data.unitIndex] || {}
    const b = this.data.blds[this.data.bldIndex] || {}
    const p = this.data.plcs[this.data.plcIndex] || {}
    return { unitId: u.id || 0, buildingId: b.id || 0, placeId: p.id || 0 }
  },

  async onPhoto() {
    try {
      const res = await wx.chooseMedia({ count: 1, mediaType: ['image'], sizeType: ['compressed'] })
      const tempPath = res.tempFiles[0].tempFilePath
      wx.getFileSystemManager().readFile({
        filePath: tempPath,
        encoding: 'base64',
        success: (r) => {
          const dataUrl = 'data:image/jpeg;base64,' + r.data
          this.setData({ photos: this.data.photos.concat([dataUrl]) })
          const org = this.orgIds()
          api.post('/photos', { dataUrl, bizType: 'hazard', bizId: 0, caption: this.data.title, unitId: org.unitId, buildingId: org.buildingId, placeId: org.placeId }).then((p) => {
            this.photoIds = (this.photoIds || []).concat([p.id])
          }).catch(() => {})
        },
      })
    } catch (e) {
      const msg = (e && (e.errMsg || e.message)) || ''
      if (msg.indexOf('privacy') >= 0) getApp().toast('需先同意隐私政策才能选择照片')
    }
  },

  removePhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photos = this.data.photos.slice()
    photos.splice(idx, 1)
    this.setData({ photos })
  },

  previewPhoto(e) {
    const idx = e.currentTarget.dataset.index
    wx.previewImage({
      current: this.data.photos[idx],
      urls: this.data.photos,
    })
  },

  async onSubmit() {
    const { title, area, level, desc, days } = this.data
    if (!title) return getApp().toast(this.data.txt.hazardTitle)
    const org = this.orgIds()
    this.setData({ submitting: true })
    try {
      await api.post('/hazards', { title, area, level, desc, days, photoIds: this.photoIds || [], unitId: org.unitId, buildingId: org.buildingId, placeId: org.placeId }, { silent: true })
      getApp().toast(i18n.t('success'), 'success')
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) { /* 已提示 */ }
    finally { this.setData({ submitting: false }) }
  },
})
