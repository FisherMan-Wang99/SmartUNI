Page({
  data: {
  studentInfo: {
  name: '学生',
  gpa: '未填写',
  testScore: '未填写',
  testScoreLabel: 'SAT',
  englishScore: '未填写',
  englishScoreLabel: '托福',
  intendedMajor: '未选择专业'
  },
  recommendations: {
  reach_schools: [],
  match_schools: [],
  safety_schools: []
  },
  recommendationReason: '',
  loading: false,
  hasData: false,
  showDebug: false
  },
  
  onLoad: function(options) {
  console.log('详情页面加载，参数:', options);
  this.fromHistory = options.fromHistory === 'true';
  this.loadData();
  },
  
  onShow: function() {
  if (!this.fromHistory) {
  this.loadData();
  }
  },
  
  loadData: function() {
  try {
  const app = getApp();
  let studentProfile = app.globalData.studentProfile || wx.getStorageSync('studentProfile') || {};
  let results = app.globalData.recommendationResults || wx.getStorageSync('recommendationResults') || {};
  
    console.log('学生档案:', studentProfile);
    console.log('推荐结果:', results);
  
    if (studentProfile && studentProfile.academics) {
      const academics = studentProfile.academics;
      const gpa = academics.gpa || '未填写';
      const sat = academics.sat || '未填写';
      const act = academics.act || '未填写';
      const toefl = academics.toefl || '未填写';
      const ielts = academics.ielts || '未填写';
      const det = academics.det || '未填写';
  
      const testScore = act !== '未填写' ? act : sat;
      const testScoreLabel = act !== '未填写' ? 'ACT' : 'SAT';
  
      let englishScore = toefl !== '未填写' ? toefl : (ielts !== '未填写' ? ielts : det);
      let englishScoreLabel = toefl !== '未填写' ? '托福' : (ielts !== '未填写' ? '雅思' : '多邻国');
  
      const studentInfo = {
        name: '学生',
        gpa,
        testScore,
        testScoreLabel,
        englishScore,
        englishScoreLabel,
        intendedMajor: studentProfile.preferences?.major || '未选择专业'
      };
  
      let recommendations = {
        reach_schools: results.reachSchools || [],
        match_schools: results.matchSchools || [],
        safety_schools: results.safetySchools || []
      };
  
      let recommendationReason = results.report || results.recommendationReason || this.generateDefaultReason(studentProfile, results);
  
      this.setData({
        studentInfo,
        recommendations,
        recommendationReason,
        hasData: true
      });
    } else {
      console.warn('没有找到学生档案数据');
      this.setDefaultStudentInfo();
    }
  } catch (error) {
    console.error('获取学生信息失败:', error);
    this.setDefaultStudentInfo();
  }
  
  },
  
  generateDefaultReason: function(studentProfile, results) {
  const academics = studentProfile.academics || {};
  const major = studentProfile.preferences?.major || '所选专业';
  const gpa = academics.gpa || '';
  const testScore = academics.act || academics.sat || '';
  let englishScore = academics.toefl || academics.ielts || academics.det || '';
  let englishScoreLabel = academics.toefl ? '托福' : academics.ielts ? '雅思' : '多邻国';
  
  let reason = `基于您的学术背景`;
  if (gpa || testScore || englishScore) {
    let scoreInfo = [];
    if (gpa) scoreInfo.push(`GPA: ${gpa}`);
    if (testScore) scoreInfo.push(`${academics.act ? 'ACT' : 'SAT'}: ${testScore}`);
    if (englishScore) scoreInfo.push(`${englishScoreLabel}: ${englishScore}`);
    reason += `（${scoreInfo.join('，')}）`;
  }
  reason += `和${major}专业意向，我们的智能推荐系统为您筛选了最合适的院校：\n\n`;
  
  const reachCount = results.reachSchools?.length || 0;
  const matchCount = results.matchSchools?.length || 0;
  const safetyCount = results.safetySchools?.length || 0;
  
  if (reachCount > 0) reason += `• 冲刺校：这些顶尖院校在${major}领域享有盛誉，虽然录取竞争激烈，但您的背景具备申请潜力；\n`;
  if (matchCount > 0) reason += `• 匹配校：这些院校与您的学术水平高度契合，在${major}专业方面提供优质教育；\n`;
  if (safetyCount > 0) reason += `• 保底校：这些院校录取把握较大，确保您有理想的入学选择。\n\n`;
  
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
  recommendations: { reach_schools: [], match_schools: [], safety_schools: [] },
  recommendationReason: '请先完成选校评估获取个性化推荐分析报告。'
  });
  },
  
  restartAssessment: function() {
  wx.navigateTo({
  url: '/pages/standard-score/standard-score'
  });
  }
  });








