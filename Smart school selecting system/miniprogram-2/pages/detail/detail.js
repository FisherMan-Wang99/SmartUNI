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
    recommendationReason: '', // 推荐原因
    loading: false,
    hasData: false,
    showDebug: false
  },

  onLoad: function(options) {
    console.log('详情页面加载，参数:', options);
    this.getStudentInfo();
  },

  onShow: function() {
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

        let recommendationReason = '';
        
        // 处理推荐结果
        if (results) {
          // 从后端的report字段获取推荐原因
          if (results.report) {
            recommendationReason = results.report;
          } else if (results.recommendationReason) {
            recommendationReason = results.recommendationReason;
          } else {
            // 如果后端没有返回推荐原因，使用默认生成
            recommendationReason = this.generateDefaultReason(studentProfile, results);
          }

          // 处理学校列表
          if (Array.isArray(results.reachSchools)) {
            recommendations.reach_schools = results.reachSchools;
          } else if (Array.isArray(results.reach_schools)) {
            recommendations.reach_schools = results.reach_schools;
          }
          
          if (Array.isArray(results.matchSchools)) {
            recommendations.match_schools = results.matchSchools;
          } else if (Array.isArray(results.match_schools)) {
            recommendations.match_schools = results.match_schools;
          }
          
          if (Array.isArray(results.safetySchools)) {
            recommendations.safety_schools = results.safetySchools;
          } else if (Array.isArray(results.safety_schools)) {
            recommendations.safety_schools = results.safety_schools;
          }
        }

        this.setData({
          studentInfo: studentInfo,
          recommendations: recommendations,
          recommendationReason: recommendationReason,
          hasData: true
        });

        console.log('从report字段获取的推荐原因:', recommendationReason);
      } else {
        console.warn('没有找到学生档案数据');
        this.setDefaultStudentInfo();
      }
    } catch (error) {
      console.error('获取学生信息失败:', error);
      this.setDefaultStudentInfo();
    }
  },

  // 生成默认推荐原因（当后端没有返回report时使用）
  generateDefaultReason: function(studentProfile, results) {
    const major = studentProfile.preferences?.major || '所选专业';
    const gpa = studentProfile.academics?.gpa || '';
    const sat = studentProfile.academics?.sat || '';
    
    let reason = `基于您的学术背景`;
    
    if (gpa || sat) {
      reason += `（${gpa ? 'GPA: ' + gpa : ''}${gpa && sat ? '，' : ''}${sat ? 'SAT: ' + sat : ''}）`;
    }
    
    reason += `和${major}专业意向，我们的智能推荐系统为您筛选了最合适的院校：\n\n`;
    
    const reachCount = results.reachSchools?.length || results.reach_schools?.length || 0;
    const matchCount = results.matchSchools?.length || results.match_schools?.length || 0;
    const safetyCount = results.safetySchools?.length || results.safety_schools?.length || 0;
    
    if (reachCount > 0) {
      reason += `• 冲刺校：这些顶尖院校在${major}领域享有盛誉，虽然录取竞争激烈，但您的背景具备申请潜力；\n`;
    }
    if (matchCount > 0) {
      reason += `• 匹配校：这些院校与您的学术水平高度契合，在${major}专业方面提供优质教育；\n`;
    }
    if (safetyCount > 0) {
      reason += `• 保底校：这些院校录取把握较大，确保您有理想的入学选择。\n\n`;
    }
    
    reason += `推荐您根据个人偏好、地理位置和校园文化等因素综合考量。`;
    
    return reason;
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
      },
      recommendationReason: '请先完成选校评估获取个性化推荐分析报告。'
    });
  },

  // 保存推荐结果（包含report）
  saveRecommendation: function() {
    wx.showModal({
      title: '保存推荐',
      content: '是否保存本次选校推荐结果和分析报告？',
      success: (res) => {
        if (res.confirm) {
          try {
            wx.setStorageSync('lastRecommendation', {
              studentInfo: this.data.studentInfo,
              recommendations: this.data.recommendations,
              recommendationReason: this.data.recommendationReason,
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

  // 跳转到历史记录页面
  navigateToHistory: function() {
    console.log('跳转到历史记录页面');
    // 使用 navigateTo 跳转
    wx.navigateTo({
      url: '/pages/history/history'
    });
    
    // 如果history页面在tabBar中，请使用下面的代码：
    // wx.switchTab({
    //   url: '/pages/history/history'
    // });
  },

  // 分享功能（包含report内容）
  onShareAppMessage: function() {
    const shareText = this.data.recommendationReason ? 
      this.data.recommendationReason.substring(0, 50) + '...' : 
      '查看我的智能选校推荐报告';
      
    return {
      title: `${this.data.studentInfo.name}的选校推荐报告`,
      desc: shareText,
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








