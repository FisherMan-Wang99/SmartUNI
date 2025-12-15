Page({
  data: {
  progress: 0, // 进度百分比
  countdownText: '1:00', // 倒计时文本
  step: 0, // 当前步骤（1-3）
  totalTime: 60, // 总等待时间（秒）
  remainingTime: 60, // 剩余时间（秒）
  intervalId: null, // 定时器ID
  currentStage: 0, // 当前阶段（0:准备, 1:分析个人资料, 2:匹配理想学校, 3:生成个性化推荐）
  stageStartTime: 0, // 阶段开始时间戳
  reportType: 'detailed', // 默认报告类型
  requestCompleted: false, // 后端请求完成标志
  fallbackTimer: null
  },
  
  onLoad: function (options) {
  this.setData({
  reportType: options.reportType || 'detailed'
  });
  
  this.startLoadingProcess();
  this.submitRequest();
  
  // 兜底机制，确保页面跳转
  this.setData({
    fallbackTimer: setTimeout(() => {
      console.log('触发兜底跳转机制');
      this.completeLoading();
    }, 65000)
  });
  
  },
  
  startLoadingProcess: function() {
  this.updateCountdown();
  this.setData({
  stageStartTime: Date.now(),
  currentStage: 1,
  step: 1
  });
  
  this.setData({
    intervalId: setInterval(() => {
      this.updateProgress();
      this.updateCountdown();
    }, 1000)
  });
  
  // 模拟步骤变化
  setTimeout(() => {
    this.setData({ step: 2, currentStage: 2, stageStartTime: Date.now() });
  }, 15000);
  
  setTimeout(() => {
    this.setData({ step: 3, currentStage: 3, stageStartTime: Date.now() });
  }, 40000);
  
  },
  
  updateProgress: function() {
  let progress = 0;
  const elapsedTime = (Date.now() - this.data.stageStartTime) / 1000;
  
  switch (this.data.currentStage) {
    case 1:
      progress = (elapsedTime / 15) * 30;
      break;
    case 2:
      progress = 30 + (elapsedTime / 25) * 60;
      break;
    case 3:
      progress = 90 + (elapsedTime / 20) * 10;
      if (elapsedTime >= 20) progress = 100;
      break;
    default:
      progress = 0;
  }
  
  progress = Math.min(progress, 100);
  this.setData({ progress: Math.round(progress) });
  
  if ((this.data.remainingTime <= 0 || progress >= 100) && this.data.requestCompleted) {
    this.completeLoading();
  }
  
  },
  
  updateCountdown: function() {
  let remaining = this.data.remainingTime - 1;
  if (remaining < 0) remaining = 0;
  
  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  const countdownText = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  
  this.setData({
    remainingTime: remaining,
    countdownText: countdownText
  });
  
  if (remaining === 0 && this.data.requestCompleted) {
    this.completeLoading();
  }
  
  },
  
  submitRequest: function() {
  const app = getApp();
  const requestData = app.globalData.studentProfile;
  const mockSchools = this.generateMockSchools();
     
  wx.request({
    url: 'https://aisel-1-204429-4-1389712700.sh.run.tcloudbase.com' + '/recommend', // 拼接完整的公网访问地址
    method: 'POST',
    header: {
      'content-type': 'application/json'
      // 注意：移除了 'X-WX-SERVICE' 请求头
    },
    data: requestData, // 原有请求数据
    timeout: 60000, // 公网调用超时可设为60秒[citation:1]
    success: (res) => {
      console.log('推荐结果获取成功 (云托管)', res);
  
      try {
        // 注意：callContainer 返回的数据结构略有不同，数据在 res.data
        const responseData = res.data;
        const results = Array.isArray(responseData.results) ? responseData.results : [];
        const report = responseData.report || "暂无推荐报告";
  
        const reachSchools = results.filter(item => item.level === "Reach");
        const matchSchools = results.filter(item => item.level === "Match");
        const safetySchools = results.filter(item => item.level === "Safety");
  
        app.globalData.recommendationResults = { report, reachSchools, matchSchools, safetySchools };
      } catch (error) {
        console.error('结果解析失败', error);
        app.globalData.recommendationResults = {
          report: "暂无推荐报告",
          reachSchools: mockSchools.reach,
          matchSchools: mockSchools.match,
          safetySchools: mockSchools.safety
        };
      }
  
      this.setData({ requestCompleted: true });
  
      // 如果进度条已满或倒计时结束，立即跳转
      if (this.data.progress >= 100 || this.data.remainingTime <= 0) {
        this.completeLoading();
      }
    },
    fail: (error) => {
      console.error('请求失败 (云托管)', error);
      app.globalData.recommendationResults = {
        report: "暂无推荐报告",
        reachSchools: mockSchools.reach,
        matchSchools: mockSchools.match,
        safetySchools: mockSchools.safety
      };
      this.setData({ requestCompleted: true });
  
      if (this.data.progress >= 100 || this.data.remainingTime <= 0) {
        this.completeLoading();
      }
    }
  });
  
  },
  
  generateMockSchools: function() {
  return {
  reach: [
  { name: "哈佛大学", location: "马萨诸塞州", acceptance_rate: "4.6%", ranking: 1, strengths: ["商科","医学","法学"], tuition: "$57,261" },
  { name: "耶鲁大学", location: "康涅狄格州", acceptance_rate: "5.9%", ranking: 3, strengths: ["法学","医学","艺术"], tuition: "$59,950" },
  { name: "麻省理工学院", location: "马萨诸塞州", acceptance_rate: "6.7%", ranking: 2, strengths: ["工程","计算机科学","物理学"], tuition: "$53,818" }
  ],
  match: [
  { name: "加州大学伯克利分校", location: "加利福尼亚州", acceptance_rate: "14.8%", ranking: 22, strengths: ["工程","计算机科学","商学"], tuition: "$44,017" },
  { name: "密歇根大学安娜堡分校", location: "密歇根州", acceptance_rate: "26.1%", ranking: 25, strengths: ["商学","医学","工程"], tuition: "$53,232" },
  { name: "北卡罗来纳大学教堂山分校", location: "北卡罗来纳州", acceptance_rate: "24.6%", ranking: 28, strengths: ["商科","医学","公共健康"], tuition: "$36,159" },
  { name: "纽约大学", location: "纽约州", acceptance_rate: "16.2%", ranking: 30, strengths: ["商学","表演艺术","法学"], tuition: "$55,350" }
  ],
  safety: [
  { name: "华盛顿大学", location: "华盛顿州", acceptance_rate: "51.8%", ranking: 59, strengths: ["计算机科学","医学","工程"], tuition: "$39,906" },
  { name: "匹兹堡大学", location: "宾夕法尼亚州", acceptance_rate: "57.5%", ranking: 58, strengths: ["医学","工程","商学"], tuition: "$34,124" },
  { name: "德克萨斯大学奥斯汀分校", location: "德克萨斯州", acceptance_rate: "32.4%", ranking: 38, strengths: ["商学","工程","计算机科学"], tuition: "$40,996" },
  { name: "伊利诺伊大学厄巴纳-香槟分校", location: "伊利诺伊州", acceptance_rate: "46.7%", ranking: 47, strengths: ["工程","计算机科学","商学"], tuition: "$36,018" }
  ]
  };
  },
  
  completeLoading: function() {
  console.log('执行completeLoading函数');
  
  if (this.data.intervalId) clearInterval(this.data.intervalId);
  if (this.data.fallbackTimer) clearTimeout(this.data.fallbackTimer);
  
  this.setData({
    progress: 100,
    countdownText: '0:00',
    step: 3,
    currentStage: 3
  });
  
  setTimeout(() => {
    const redirectUrl = `/pages/detail/detail?reportType=${this.data.reportType}`;
    wx.reLaunch({
      url: redirectUrl,
      fail: (res) => {
        console.error('页面跳转失败', res);
        wx.redirectTo({ url: redirectUrl, fail: (err) => console.error('redirectTo也失败', err) });
      },
      success: () => console.log('页面跳转成功')
    });
  }, 800);
  
  },
  
  onUnload: function () {
  if (this.data.intervalId) clearInterval(this.data.intervalId);
  if (this.data.fallbackTimer) clearTimeout(this.data.fallbackTimer);
  }
  });