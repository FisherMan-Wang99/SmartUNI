Page({
  data: {
    gpa: "",
    sat: "",
    toefl: "",
    background: "",
    preference: "",
    personality: "",
    climate: "",
    results: [],
    reachSchools: [],
    matchSchools: [],
    safetySchools: [],
    loading: false,
    noData: false,

    // 下拉选项
    backgroundOptions: ["无研究经历", "参与小型项目", "校内科研助理", "发表过论文"],
    preferenceOptions: ["学术研究型（如常春藤）", "工程技术强校", "商业/金融中心", "综合性大学", "国际化都市"],
    personalityOptions: ["INTJ（战略家）", "ENTP（辩论家）", "INFJ（提倡者）", "ENFP（竞选者）", "ISTJ（物流师）", "ESTJ（执行官）", "ISFP（探险家）", "ESFP（表演者）"],
    climateOptions: ["温暖阳光（南加州/佛罗里达）", "四季分明（东北/中西部）", "凉爽宜人（西北/新英格兰）"],
  },

  // 输入事件
  onInputGPA(e) { this.setData({ gpa: e.detail.value }); },
  onInputSAT(e) { this.setData({ sat: e.detail.value }); },
  onInputTOEFL(e) { this.setData({ toefl: e.detail.value }); },

  // Picker选择
  onBackgroundChange(e) { this.setData({ background: this.data.backgroundOptions[e.detail.value] }); },
  onPreferenceChange(e) { this.setData({ preference: this.data.preferenceOptions[e.detail.value] }); },
  onPersonalityChange(e) { this.setData({ personality: this.data.personalityOptions[e.detail.value] }); },
  onClimateChange(e) { this.setData({ climate: this.data.climateOptions[e.detail.value] }); },

  // 提交
  onSubmit() {
    const { gpa, sat, toefl, background, preference, personality, climate } = this.data;
    let missing = [];
    if (!gpa) missing.push("GPA");
    if (!sat) missing.push("SAT");
    if (!toefl) missing.push("TOEFL");
    if (!background) missing.push("研究经历");
    if (!preference) missing.push("偏好");
    if (!personality) missing.push("性格");
    if (!climate) missing.push("气候");

    if (missing.length > 0) {
      wx.showModal({ title: "提示", content: "请填写: " + missing.join("、"), showCancel: false });
      return;
    }

    this.setData({ loading: true, results: [], noData: false });

    wx.request({
      url: "http://192.168.3.99:8000/recommend",
      method: "POST",
      header: { "Content-Type": "application/json" },
      data: {
        academics: { gpa, sat, toefl },
        background: { research: background, internship: "None", extracurricular: [] },
        preferences: { location: preference, size: "Medium", climate },
        personality: { type: personality, traits: ["curious"] }
      },
      success: (res) => {
        console.log("后端返回:", res.data);
        this.setData({ loading: false });
      
        const report = res.data.report || "暂无推荐报告";
        const results = Array.isArray(res.data.results) ? res.data.results : [];
      
        const reachSchools = results.filter(item => item.level === "Reach");
        const matchSchools = results.filter(item => item.level === "Match");
        const safetySchools = results.filter(item => item.level === "Safety");
      
        // 保存到本地存储
        wx.setStorageSync('schoolData', { report, reachSchools, matchSchools, safetySchools });
      
        // 跳转
        wx.navigateTo({
          url: '/pages/detail/detail'
        });
      },
      
      fail: (err) => {
        console.error("请求失败:", err);
        this.setData({ loading: false });
        wx.showToast({ title: "请求失败，请检查后端地址或网络", icon: "none" });
      }
      
    });
  },

});





