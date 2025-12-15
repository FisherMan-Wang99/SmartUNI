// app.js
App({
  onLaunch: function () {
    // 初始化云托管调用能力（新增）
    wx.cloud.init()
    // 这里可以放其他你原本的初始化逻辑...
  },

  globalData: {
    // 这里只存储需要跨页面共享的数据
    studentProfile: null,
    recommendationResults: null
  }
})