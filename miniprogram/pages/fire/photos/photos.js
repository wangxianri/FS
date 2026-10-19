// 随手拍（带点位选择）
const api = require('../../../utils/api')
const orgSel = require('../../../utils/org-select')
const fmt = require('../../../utils/format')
const i18n = require('../../../utils/i18n')

// 预计算文案（wxml 不支持调用 data 中的函数，必须提前算好）
function texts() {
  return {
    selectUnit: i18n.t('selectUnit'),
    selectBuilding: i18n.t('selectBuilding'),
    selectPlace: i18n.t('selectPlace'),
    note: i18n.t('note'),
    loading: i18n.t('loading'),
    photos: i18n.t('photos'),
    noData: i18n.t('noData'),
  }
}

Page({
  data: {
    org: orgSel.orgData(),
    photos: [],
    caption: '',
    uploading: false,
    loading: true,
    txt: texts(),
  },

  onLoad() {
    orgSel.init(this)
  },
  onShow() { this.load() },

  async load() {
    try {
      const photos = await api.get('/photos', {}, { silent: true })
      const mapped = (photos || []).map((p) => ({ ...p, createdAtText: fmt.datetime(p.created_at) }))
      this.setData({ photos: mapped, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },

  onUnit(e) { orgSel.onUnit(this, { detail: { value: e.detail.index } }) },
  onBld(e) { orgSel.onBld(this, { detail: { value: e.detail.index } }) },
  onPlc(e) { orgSel.onPlc(this, { detail: { value: e.detail.index } }) },

  onCaption(e) { this.setData({ caption: e.detail.value }) },

  async onUpload() {
    const { caption } = this.data
    const { unitId, buildingId, placeId } = orgSel.ids(this)
    if (!unitId) return getApp().toast(i18n.t('selectUnit'))
    try {
      const res = await wx.chooseMedia({ count: 1, mediaType: ['image'], sizeType: ['compressed'] })
      const tempPath = res.tempFiles[0].tempFilePath
      this.setData({ uploading: true })
      wx.getFileSystemManager().readFile({
        filePath: tempPath,
        encoding: 'base64',
        success: async (r) => {
          const dataUrl = 'data:image/jpeg;base64,' + r.data
          await api.post('/photos', { dataUrl, bizType: 'general', caption, unitId, buildingId, placeId }, { silent: true })
          getApp().toast(i18n.t('success'), 'success')
          this.setData({ caption: '', uploading: false })
          this.load()
        },
        fail: () => this.setData({ uploading: false }),
      })
    } catch (e) {
      // 用户拒绝隐私授权时给出引导
      const msg = (e && (e.errMsg || e.message)) || ''
      if (msg.indexOf('privacy') >= 0) getApp().toast('需先同意隐私政策才能选择照片')
    }
  },

  preview(e) {
    const idx = e.currentTarget.dataset.index
    const urls = this.data.photos.map((p) => p.data_url)
    if (urls.length) wx.previewImage({ urls, current: urls[idx] })
  },
})