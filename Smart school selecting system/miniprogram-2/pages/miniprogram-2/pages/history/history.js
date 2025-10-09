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

  // 加载历史数据
  loadHistoryData: function() {
    this.setData({ loading: true });

    // 模拟加载延迟，使加载体验更流畅
    setTimeout(() => {
      try {
        // 从本地存储读取历史记录
        const historyList = wx.getStorageSync('recommendationHistory') || [];
        
        // 如果没有历史记录，创建一些示例数据以便测试
        if (historyList.length === 0) {
          const mockData = [
            {
              id: Date.now() - 86400000, // 昨天
              createTime: this.formatDateTime(new Date(Date.now() - 86400000)),
              status: 'success',
              statusText: '已完成',
              targetMajor: '计算机科学',
              targetDegree: '硕士',
              totalSchools: 8,
              avgMatchRate: 78,
              fullData: {
                studentInfo: {
                  name: '示例学生',
                  gpa: '3.8',
                  testScore: '1500',
                  testScoreLabel: 'SAT',
                  englishScore: '105',
                  englishScoreLabel: '托福',
                  intendedMajor: '计算机科学'
                },
                recommendations: {
                  reach_schools: [{name: '麻省理工学院'}],
                  match_schools: [{name: '加州大学洛杉矶分校'}],
                  safety_schools: [{name: '加州大学欧文分校'}]
                },
                recommendationReason: '示例推荐原因'
              }
            },
            {
              id: Date.now() - 172800000, // 前天
              createTime: this.formatDateTime(new Date(Date.now() - 172800000)),
              status: 'success',
              statusText: '已完成',
              targetMajor: '数据科学',
              targetDegree: '硕士',
              totalSchools: 6,
              avgMatchRate: 85,
              fullData: {
                studentInfo: {
                  name: '示例学生',
                  gpa: '3.9',
                  testScore: '32',
                  testScoreLabel: 'ACT',
                  englishScore: '7.5',
                  englishScoreLabel: '雅思',
                  intendedMajor: '数据科学'
                },
                recommendations: {
                  reach_schools: [{name: '斯坦福大学'}],
                  match_schools: [{name: '加州大学伯克利分校'}],
                  safety_schools: [{name: '加州大学圣地亚哥分校'}]
                },
                recommendationReason: '示例推荐原因'
              }
            }
          ];
          // 保存示例数据到本地存储
          wx.setStorageSync('recommendationHistory', mockData);
          this.setData({
            historyList: mockData,
            loading: false
          });
        } else {
          this.setData({
            historyList: historyList,
            loading: false
          });
        }
      } catch (e) {
        console.error('加载历史记录失败:', e);
        this.setData({
          historyList: [],
          loading: false
        });
        wx.showToast({
          title: '加载历史记录失败',
          icon: 'none'
        });
      }
    }, 500);
  },
  
  // 格式化日期时间
  formatDateTime: function(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  },

  // 点击历史记录项
  onItemClick: function(e) {
    const item = e.currentTarget.dataset.item;
    console.log('点击历史记录:', item);
    
    try {
      // 将选中的历史记录数据保存到全局变量
      const app = getApp();
      
      // 确保有完整的数据可以恢复
      if (item.fullData) {
        app.globalData.studentProfile = item.fullData.studentProfile || {
          academics: {
            gpa: item.fullData.studentInfo?.gpa,
            sat: item.fullData.studentInfo?.testScoreLabel === 'SAT' ? item.fullData.studentInfo?.testScore : null,
            act: item.fullData.studentInfo?.testScoreLabel === 'ACT' ? item.fullData.studentInfo?.testScore : null,
            toefl: item.fullData.studentInfo?.englishScoreLabel === '托福' ? item.fullData.studentInfo?.englishScore : null,
            ielts: item.fullData.studentInfo?.englishScoreLabel === '雅思' ? item.fullData.studentInfo?.englishScore : null,
            det: item.fullData.studentInfo?.englishScoreLabel === '多邻国' ? item.fullData.studentInfo?.englishScore : null
          },
          preferences: {
            major: item.fullData.studentInfo?.intendedMajor
          }
        };
        
        app.globalData.recommendationResults = item.fullData.recommendationResults || {
          report: item.fullData.recommendationReason,
          reachSchools: item.fullData.recommendations?.reach_schools || [],
          matchSchools: item.fullData.recommendations?.match_schools || [],
          safetySchools: item.fullData.recommendations?.safety_schools || []
        };
        
        // 跳转到详情页
        wx.navigateTo({
          url: '/pages/detail/detail?fromHistory=true'
        });
      } else {
        wx.showToast({
          title: '数据不完整，无法查看详情',
          icon: 'none'
        });
      }
    } catch (e) {
      console.error('查看历史记录详情失败:', e);
      wx.showToast({
        title: '查看详情失败',
        icon: 'none'
      });
    }
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