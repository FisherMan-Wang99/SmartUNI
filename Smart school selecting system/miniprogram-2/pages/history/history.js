// pages/history/history.js
Page({
  data: {
    historyList: [], // 历史记录列表
    loading: false,  // 加载状态
  },

  onLoad: function(options) {
    // 页面加载时调用
    this.loadHistoryData();
  },

  onShow: function() {
    // 页面显示时调用
    // 您可以在这里添加数据刷新逻辑
  },

  onPullDownRefresh: function() {
    // 下拉刷新
    console.log('下拉刷新');
    this.loadHistoryData();
    wx.stopPullDownRefresh();
  },

  // 加载历史数据 - 这里使用模拟数据，您后续可以替换为真实数据
  loadHistoryData: function() {
    this.setData({ loading: true });

    // 模拟加载延迟
    setTimeout(() => {
      // 这里是模拟数据，您后续可以替换为从globalData或缓存读取
      const mockData = [
        {
          id: 1,
          createTime: '2024-01-15 14:30',
          status: 'success',
          statusText: '已完成',
          targetMajor: '计算机科学',
          targetDegree: '硕士',
          totalSchools: 8,
          avgMatchRate: 78
        },
        {
          id: 2,
          createTime: '2024-01-14 10:15',
          status: 'success',
          statusText: '已完成',
          targetMajor: '数据科学',
          targetDegree: '硕士',
          totalSchools: 6,
          avgMatchRate: 85
        }
      ];

      this.setData({
        historyList: mockData,
        loading: false
      });
    }, 1000);
  },

  // 点击历史记录项
  onItemClick: function(e) {
    const item = e.currentTarget.dataset.item;
    console.log('点击历史记录:', item);
    
    // 这里您可以添加跳转到详情页的逻辑
    wx.showToast({
      title: '跳转到详情页',
      icon: 'none'
    });
  },

  // 前往生成推荐页面
  goToGenerate: function() {
    console.log('前往生成推荐');
    // 这里您可以添加跳转到首页或评估页面的逻辑
    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  // 分享功能
  onShareAppMessage: function() {
    return {
      title: '我的选校历史记录',
      path: '/pages/history/history'
    };
  }
});