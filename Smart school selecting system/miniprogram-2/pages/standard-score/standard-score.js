// pages/standard-score/standard-score.js
Page({
  data: {
    gpa: "",
    testType: "",
    testScore: "",
    englishTestType: "",
    englishScore: "",

    testTypeOptions: ["SAT", "ACT"],
    englishTestOptions: ["托福(TOEFL)", "雅思(IELTS)", "多邻国(DET)"]
  },

  onLoad() {
    const app = getApp();

    // 如果之前填写过，则恢复数据
    const saved = app.globalData?.formData?.standardScore;
    if (saved) {
      this.setData({
        gpa: saved.gpa || "",
        testType: saved.testType || "",
        testScore: saved.testScore || "",
        englishTestType: saved.englishTestType || "",
        englishScore: saved.englishScore || ""
      });
    }
  },

  // 输入事件
  onInputGPA(e) { this.setData({ gpa: e.detail.value }); },
  onInputTestScore(e) { this.setData({ testScore: e.detail.value }); },
  onInputEnglishScore(e) { this.setData({ englishScore: e.detail.value }); },

  // picker事件
  onTestTypeChange(e) {
    this.setData({ testType: this.data.testTypeOptions[e.detail.value] });
  },
  onEnglishTestTypeChange(e) {
    this.setData({ englishTestType: this.data.englishTestOptions[e.detail.value] });
  },

  // 下一步
  goToNext() {
    const app = getApp();

    // 确保 formData 初始化
    if (!app.globalData.formData) app.globalData.formData = {};

    // 保存原始成绩
    app.globalData.formData.standardScore = {
      gpa: this.data.gpa,
      testType: this.data.testType,
      testScore: this.data.testScore,
      englishTestType: this.data.englishTestType,
      englishScore: this.data.englishScore
    };

    // === 统一格式化为后端 + detail 页使用的结构 ===
    const academics = {
      gpa: this.data.gpa || null,
      sat: this.data.testType === "SAT" ? this.data.testScore : null,
      act: this.data.testType === "ACT" ? this.data.testScore : null,
      toefl: this.data.englishTestType.includes("托福") ? this.data.englishScore : null,
      ielts: this.data.englishTestType.includes("雅思") ? this.data.englishScore : null,
      det: this.data.englishTestType.includes("多邻国") ? this.data.englishScore : null
    };

    if (!app.globalData.studentProfile)
      app.globalData.studentProfile = { academics: {} };

    app.globalData.studentProfile.academics = academics;

    console.log("【标准成绩写入成功】", academics);

    wx.navigateTo({
      url: "/pages/activities/activities"
    });
  }
});
