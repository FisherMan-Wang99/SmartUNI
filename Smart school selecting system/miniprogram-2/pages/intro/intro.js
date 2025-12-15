// pages/intro/intro.js
Page({

  /**
   * 页面的初始数据
   */
  data: {
  },

  /**
   * 返回上一页
   */
  goBack: function() {
    wx.navigateBack();
  },

  /**
   * 跳转到信息填写页面
   */
  goToIndex: function(e) {
    // 创建波纹动画效果
    const btn = e.currentTarget;
    
    // 触发波纹动画的CSS类
    this.setData({
      animatingBtn: true
    });
    
    // 延迟跳转，让用户看到动画效果
    setTimeout(() => {
      wx.navigateTo({
        url: '/pages/standard-score/standard-score'
      });
      // 重置动画状态
      this.setData({
        animatingBtn: false
      });
    }, 300);
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad: function (options) {
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady: function () {
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow: function () {
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide: function () {
  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload: function () {
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh: function () {
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom: function () {
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage: function () {
  }
})