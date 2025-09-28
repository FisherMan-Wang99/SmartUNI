// pages/detail/detail.js
Page({
  data: {
    studentInfo: {
      name: '学生',
      gpa: '未填写',
      sat: '未填写',
      toefl: '未填写',
      intendedMajor: '未选择专业'
    },
    recommendations: {
      reach_schools: [],
      match_schools: [],
      safety_schools: []
    },
    loading: false,
    hasData: false,
    showDebug: false // 控制调试信息显示
  },

  onLoad: function(options) {
    console.log('详情页面加载，参数:', options);
    this.getStudentInfo();
  },

  onShow: function() {
    // 页面显示时重新检查数据
    this.getStudentInfo();
  },

  // 安全地获取学生信息
  getStudentInfo: function() {
    try {
      const app = getApp();
      console.log('全局数据:', app.globalData);
      
      if (!app || !app.globalData) {
        console.warn('globalData 未初始化');
        this.setDefaultStudentInfo();
        return;
      }

      const studentProfile = app.globalData.studentProfile;
      const results = app.globalData.recommendationResults;

      console.log('学生档案:', studentProfile);
      console.log('推荐结果:', results);

      if (studentProfile) {
        const studentInfo = {
          name: '学生',
          gpa: studentProfile.academics?.gpa || '未填写',
          sat: studentProfile.academics?.sat || '未填写',
          toefl: studentProfile.academics?.toefl || '未填写',
          intendedMajor: studentProfile.preferences?.major || '未选择专业'
        };

        let recommendations = {
          reach_schools: [],
          match_schools: [],
          safety_schools: []
        };

        // 处理推荐结果
        if (results) {
          if (Array.isArray(results.reachSchools)) {
            recommendations.reach_schools = results.reachSchools;
          }
          if (Array.isArray(results.matchSchools)) {
            recommendations.match_schools = results.matchSchools;
          }
          if (Array.isArray(results.safetySchools)) {
            recommendations.safety_schools = results.safetySchools;
          }
        }

        this.setData({
          studentInfo: studentInfo,
          recommendations: recommendations,
          hasData: true
        });

        console.log('设置后的数据:', this.data);
      } else {
        console.warn('没有找到学生档案数据');
        this.setDefaultStudentInfo();
      }
    } catch (error) {
      console.error('获取学生信息失败:', error);
      this.setDefaultStudentInfo();
    }
  },

  setDefaultStudentInfo: function() {
    this.setData({
      hasData: false,
      studentInfo: {
        name: '请先填写信息',
        gpa: '暂无',
        sat: '暂无',
        toefl: '暂无',
        intendedMajor: '暂无'
      },
      recommendations: {
        reach_schools: [],
        match_schools: [],
        safety_schools: []
      }
    });
  },

  // 保存推荐结果
  saveRecommendation: function() {
    wx.showModal({
      title: '保存推荐',
      content: '是否保存本次选校推荐结果？',
      success: (res) => {
        if (res.confirm) {
          try {
            wx.setStorageSync('lastRecommendation', {
              studentInfo: this.data.studentInfo,
              recommendations: this.data.recommendations,
              timestamp: new Date().getTime()
            });
            wx.showToast({
              title: '保存成功',
              icon: 'success'
            });
          } catch (e) {
            console.error('保存失败:', e);
            wx.showToast({
              title: '保存失败',
              icon: 'none'
            });
          }
        }
      }
    });
  },

  // 分享功能
  shareRecommendation: function() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage: function() {
    return {
      title: `${this.data.studentInfo.name}的智能选校推荐结果`,
      path: '/pages/detail/detail',
      imageUrl: '/images/share-cover.png'
    };
  },

  // 调试功能
  toggleDebug: function() {
    this.setData({
      showDebug: !this.data.showDebug
    });
  },

  // 下拉刷新
  onPullDownRefresh: function() {
    console.log('下拉刷新');
    this.getStudentInfo();
    wx.stopPullDownRefresh();
  }
});






