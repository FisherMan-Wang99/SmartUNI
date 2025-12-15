Page({
  data: {
    // 封面页面数据
  },

  onLoad() {
    console.log('云道智能选校封面页面加载');
  },

  onShow() {
    // 页面显示时的逻辑
  },
 
  // 跳转到介绍页面
  goToIndex() {
    wx.navigateTo({
      url: '/pages/intro/intro',
      success: () => {
        console.log('成功跳转到介绍页面');
      },
      fail: (err) => {
        console.error('跳转失败:', err);
        wx.showToast({
          title: '跳转失败',
          icon: 'none'
        });
      }
    });
  }
});
