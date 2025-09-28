// pages/index/index.js
Page({
  // 页面数据 - 用于视图绑定
  data: {
    gpa: "",
    sat: "",
    toefl: "",
    background: "",
    preference: "",
    personality: "",
    personalityType: "",
    climate: "",
    extracurricular: "",
    major: "",
    teachingStyle: "",
    internship: "",
    location: "",
    size: "",
    schoolType: "",
    loading: false,
    noData: false,

    // 下拉选项 - 这些是页面渲染需要的，应该放在data中
    backgroundOptions: ["无研究经历", "参与小型项目", "校内科研助理", "发表过论文"],
    preferenceOptions: ["学术研究型（如常春藤）", "工程技术强校", "商业/金融中心", "综合性大学", "国际化都市"],
    personalityOptions: [
      "INTJ（战略家）", "ENTP（辩论家）", "INFJ（提倡者）", "ENFP（竞选者）",
      "ISTJ（物流师）", "ESTJ（执行官）", "ISFP（探险家）", "ESFP（表演者）"
    ],
    personalityTypeOptions: ["领导型", "创新型", "分析型", "社交型", "执行型", "支持型"],
    climateOptions: ["温暖阳光（南加州/佛罗里达）", "四季分明（东北/中西部）", "凉爽宜人（西北/新英格兰）"],
    extracurricularOptions: ["电影俱乐部", "学生会/学生组织", "志愿服务", "体育队", "音乐/美术社团"],
    majorOptions: ["计算机科学", "工程学", "商业/金融", "艺术/电影", "生物学", "心理学"],
    teachingStyleOptions: ["理论导向", "实践导向", "项目驱动", "专业/网络导向"],
    internshipOptions: ["无实习", "校内实习", "企业实习", "科研实习"],
    locationOptions: ["城市", "郊区", "乡村"],
    sizeOptions: ["小型", "中型", "大型"],
    schoolTypeOptions: ["研究型", "文理学院", "综合大学"]
  },

  // 输入事件 - 这些修改页面数据
  onInputGPA(e) { this.setData({ gpa: e.detail.value }); },
  onInputSAT(e) { this.setData({ sat: e.detail.value }); },
  onInputTOEFL(e) { this.setData({ toefl: e.detail.value }); },

  // Picker选择事件
  onBackgroundChange(e) { 
    this.setData({ 
      background: this.data.backgroundOptions[e.detail.value] 
    }); 
  },
  onPreferenceChange(e) { this.setData({ preference: this.data.preferenceOptions[e.detail.value] }); },
  onPersonalityChange(e) { this.setData({ personality: this.data.personalityOptions[e.detail.value] }); },
  onPersonalityTypeChange(e) { this.setData({ personalityType: this.data.personalityTypeOptions[e.detail.value] }); },
  onClimateChange(e) { this.setData({ climate: this.data.climateOptions[e.detail.value] }); },
  onExtracurricularChange(e) { this.setData({ extracurricular: this.data.extracurricularOptions[e.detail.value] }); },
  onMajorChange(e) { this.setData({ major: this.data.majorOptions[e.detail.value] }); },
  onTeachingStyleChange(e) { this.setData({ teachingStyle: this.data.teachingStyleOptions[e.detail.value] }); },
  onInternshipChange(e) { this.setData({ internship: this.data.internshipOptions[e.detail.value] }); },
  onLocationChange(e) { this.setData({ location: this.data.locationOptions[e.detail.value] }); },
  onSizeChange(e) { this.setData({ size: this.data.sizeOptions[e.detail.value] }); },
  onSchoolTypeChange(e) { this.setData({ schoolType: this.data.schoolTypeOptions[e.detail.value] }); },

  // 提交
  onSubmit() {
    const { gpa, sat, toefl, background, preference, personality, personalityType, climate,
            extracurricular, major, teachingStyle, internship, location, size, schoolType } = this.data;

    // 验证逻辑保持不变
    let missing = [];
    if (!gpa) missing.push("GPA");
    if (!sat) missing.push("SAT");
    if (!toefl) missing.push("TOEFL");
    if (!background) missing.push("研究经历");
    if (!preference) missing.push("偏好");
    if (!personality) missing.push("性格");
    if (!personalityType) missing.push("性格类别");
    if (!climate) missing.push("气候");
    if (!extracurricular) missing.push("课外活动");
    if (!major) missing.push("专业");
    if (!teachingStyle) missing.push("教学风格");
    if (!internship) missing.push("实习经历");
    if (!location) missing.push("学校位置");
    if (!size) missing.push("学校规模");

    if (missing.length > 0) {
      wx.showModal({ title: "提示", content: "请填写: " + missing.join("、"), showCancel: false });
      return;
    }

    this.setData({ loading: true });

    // 准备发送到后端的数据
    const requestData = {
      academics: { gpa, sat, toefl },
      background: { research: background, internship, extracurricular: [extracurricular] },
      preferences: { location, size, climate, major, teaching_style: teachingStyle, type: schoolType },
      personality: { type: personalityType, traits: personality  }
    };

    // 保存到全局数据，供详情页使用
    const app = getApp();
    app.globalData.studentProfile = requestData;

    wx.request({
      url: "http://192.168.3.99:8000/recommend",
      timeout: 300000,
      method: "POST",
      header: { "Content-Type": "application/json" },
      data: requestData,
      // 在 index.js 的请求成功回调中
      success: (res) => {
        console.log("后端返回完整数据:", res.data);
        this.setData({ loading: false });

        // 确保正确解析后端数据
        const results = Array.isArray(res.data.results) ? res.data.results : [];
        const report = res.data.report || "暂无推荐报告";

        console.log("解析后的结果:", results);

        // 按等级分类
        const reachSchools = results.filter(item => item.level === "Reach");
        const matchSchools = results.filter(item => item.level === "Match");
        const safetySchools = results.filter(item => item.level === "Safety");

        console.log("分类结果:", { reachSchools, matchSchools, safetySchools });

        // 保存到全局数据
        const app = getApp();
        app.globalData.recommendationResults = {
          report,
          reachSchools,
          matchSchools,
          safetySchools
        };

        // 跳转到详情页
        wx.navigateTo({ url: '/pages/detail/detail' });
      },
      fail: (err) => {
        console.error("请求失败:", err);
        this.setData({ loading: false });
        wx.showToast({ title: "请求失败，请检查后端地址或网络", icon: "none" });
      }
    });
  }
});








