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
    this.fromHistory = options.fromHistory === 'true';
    this.getStudentInfo();
  },

  onShow: function() {
    // 如果是从历史记录页面过来的，不再重新获取数据
    if (!this.fromHistory) {
      this.getStudentInfo();
    }
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
        // 确定要显示的考试成绩类型（SAT/ACT）
        const testScoreType = studentProfile.academics?.act ? 'act' : 'sat';
        const testScoreLabel = testScoreType.toUpperCase();
        const testScore = studentProfile.academics?.[testScoreType] || '未填写';
        
        // 确定要显示的英语考试类型
        let englishScoreLabel = '托福';
        let englishScore = studentProfile.academics?.toefl || '未填写';
        
        if (studentProfile.academics?.ielts) {
          englishScoreLabel = '雅思';
          englishScore = studentProfile.academics.ielts;
        } else if (studentProfile.academics?.det) {
          englishScoreLabel = '多邻国';
          englishScore = studentProfile.academics.det;
        }
        
        const studentInfo = {
          name: '学生',
          gpa: studentProfile.academics?.gpa || '未填写',
          testScore: testScore,
          testScoreLabel: testScoreLabel,
          englishScore: englishScore,
          englishScoreLabel: englishScoreLabel,
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
    
    // 确定要显示的考试成绩
    const testScoreType = studentProfile.academics?.act ? 'ACT' : 'SAT';
    const testScore = studentProfile.academics?.act || studentProfile.academics?.sat || '';
    
    // 确定要显示的英语考试成绩
    let englishScoreLabel = '托福';
    let englishScore = studentProfile.academics?.toefl || '';
    
    if (studentProfile.academics?.ielts) {
      englishScoreLabel = '雅思';
      englishScore = studentProfile.academics.ielts;
    } else if (studentProfile.academics?.det) {
      englishScoreLabel = '多邻国';
      englishScore = studentProfile.academics.det;
    }
    
    let reason = `基于您的学术背景`;
    
    if (gpa || testScore || englishScore) {
      let scoreInfo = [];
      if (gpa) scoreInfo.push(`GPA: ${gpa}`);
      if (testScore) scoreInfo.push(`${testScoreType}: ${testScore}`);
      if (englishScore) scoreInfo.push(`${englishScoreLabel}: ${englishScore}`);
      reason += `（${scoreInfo.join('，')}）`;
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
        testScore: '暂无',
        testScoreLabel: 'SAT',
        englishScore: '暂无',
        englishScoreLabel: '托福',
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

  // 保存推荐结果到历史记录
  saveRecommendation: function() {
    wx.showModal({
      title: '保存推荐',
      content: '是否保存本次选校推荐结果和分析报告？',
      success: (res) => {
        if (res.confirm) {
          try {
            // 获取现有的历史记录
            const historyList = wx.getStorageSync('recommendationHistory') || [];
            
            // 创建新的历史记录项
            const newRecord = {
              id: Date.now(), // 使用时间戳作为唯一ID
              createTime: this.formatDateTime(new Date()),
              status: 'success',
              statusText: '已完成',
              targetMajor: this.data.studentInfo.intendedMajor,
              targetDegree: '硕士', // 假设为硕士，可根据实际情况修改
              totalSchools: (
                (this.data.recommendations.reach_schools?.length || 0) +
                (this.data.recommendations.match_schools?.length || 0) +
                (this.data.recommendations.safety_schools?.length || 0)
              ),
              avgMatchRate: 80, // 默认值，可根据实际情况计算
              // 保存完整的数据以便后续查看
              fullData: {
                studentInfo: this.data.studentInfo,
                recommendations: this.data.recommendations,
                recommendationReason: this.data.recommendationReason,
                timestamp: new Date().getTime(),
                studentProfile: getApp().globalData.studentProfile,
                recommendationResults: getApp().globalData.recommendationResults
              }
            };
            
            // 添加到历史记录列表开头
            historyList.unshift(newRecord);
            
            // 保存到本地存储
            wx.setStorageSync('recommendationHistory', historyList);
            
            // 同时保存为最后一次推荐（保持向后兼容）
            wx.setStorageSync('lastRecommendation', newRecord.fullData);
            
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
  
  // 格式化日期时间
  formatDateTime: function(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
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








