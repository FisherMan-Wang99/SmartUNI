// pages/index/index.js
Page({
  // 页面数据 - 用于视图绑定
  data: {
    gpa: "",
    sat: "",
    act: "",
    testType: "", // 添加考试类型（SAT或ACT）
    testScore: "", // 添加通用考试成绩字段
    englishTestType: "", // 添加英语考试类型
    englishScore: "",   // 添加通用英语成绩字段
    
    // 活动经历 - 时长（月）
    researchExperience: "", // 课外科研时长（月）
    volunteerExperience: "", // 志愿者活动时长（月）
    internshipExperience: "", // 兼职、实习经历时长（月）
    artPractice: "", // 艺术实践、练习时长（月）
    fullTimeWork: "", // 全职工作时长（月）
    honors: "", // 校级及以上荣誉
    
    // 活动类型选择
    researchType: "", // 课外科研类型
    volunteerType: "", // 志愿者活动类型
    internshipType: "", // 兼职、实习类型
    artPracticeType: "", // 艺术实践类型
    fullTimeWorkType: "", // 全职工作类型
    
    // 学校偏好
    careerInterest: "", // 职业兴趣
    location: "", // 位置
    schoolSize: "", // 规模
    tuition: 150000, // 学费（默认值）
    major: "", // 专业
    teacherStudentRatio: "", // 师生关系
    schoolAtmosphere: "", // 学校氛围
    internationalLevel: "", // 国际化程度
    
    loading: false,
    noData: false,
  
    // 下拉选项
    careerInterestOptions: ["做科研、进大学、企业科研部门当老师、研发人员", "毕业后进市场找工作", "创业"],
    locationOptions: ["大城市", "城市", "无所谓", "边郊", "乡村/大学城"],
    schoolSizeOptions: ["巨大（50，000+）", "大（20，000+）", "正常（10，000+）", "偏小（5，000+）", "小（<5，000）"],
    teacherStudentRatioOptions: ["更关心（师生比高）", "更摸鱼/自主（师生比低）"],
    schoolAtmosphereOptions: ["Party School", "Neutral", "Nerdy School"],
    internationalLevelOptions: ["高", "低"],
    majorOptions: ["计算机科学", "工程学", "商业/金融", "艺术/电影", "生物学", "心理学"],
    englishTestOptions: ["托福(TOEFL)", "雅思(IELTS)", "多邻国(DET)"], // 添加英语考试选项
    testTypeOptions: ["SAT", "ACT"], // 添加考试类型选项（SAT或ACT）
    
    // 活动类型选项
    researchTypeOptions: ["校内科研项目", "校外科研实习", "学术竞赛", "独立研究", "其他"],
    volunteerTypeOptions: ["公益组织", "学校社团", "社区服务", "环保活动", "其他"],
    internshipTypeOptions: ["科技公司", "金融机构", "教育机构", "文创产业", "自主创业/公众号", "其他"],
    artPracticeTypeOptions: ["音乐", "美术", "舞蹈", "戏剧", "数字艺术", "其他"],
    fullTimeWorkTypeOptions: ["科技行业", "金融行业", "教育行业", "医疗行业", "政府机构", "其他"]
  },

  // 输入事件
  onInputGPA(e) { this.setData({ gpa: e.detail.value }); },
  onInputTestScore(e) { this.setData({ testScore: e.detail.value }); }, // 通用考试成绩输入处理
  onInputEnglishScore(e) { this.setData({ englishScore: e.detail.value }); }, // 英语成绩输入处理
  
  // 活动经历输入事件
  onInputResearchExperience(e) { this.setData({ researchExperience: e.detail.value }); },
  onInputVolunteerExperience(e) { this.setData({ volunteerExperience: e.detail.value }); },
  onInputInternshipExperience(e) { this.setData({ internshipExperience: e.detail.value }); },
  onInputArtPractice(e) { this.setData({ artPractice: e.detail.value }); },
  onInputFullTimeWork(e) { this.setData({ fullTimeWork: e.detail.value }); },
  onInputHonors(e) { this.setData({ honors: e.detail.value }); },
  
  // 学费滑块变化
  onTuitionChange(e) { this.setData({ tuition: e.detail.value }); },

  // Picker选择事件
  onTestTypeChange(e) { 
    this.setData({ 
      testType: this.data.testTypeOptions[e.detail.value] 
    }); 
  }, 
  onEnglishTestTypeChange(e) { 
    this.setData({ 
      englishTestType: this.data.englishTestOptions[e.detail.value] 
    }); 
  },
  onCareerInterestChange(e) { 
    this.setData({ 
      careerInterest: this.data.careerInterestOptions[e.detail.value] 
    }); 
  }, 
  onLocationChange(e) { 
    this.setData({ 
      location: this.data.locationOptions[e.detail.value] 
    }); 
  }, 
  onSchoolSizeChange(e) { 
    this.setData({ 
      schoolSize: this.data.schoolSizeOptions[e.detail.value] 
    }); 
  },
  onTeacherStudentRatioChange(e) { 
    this.setData({ 
      teacherStudentRatio: this.data.teacherStudentRatioOptions[e.detail.value] 
    }); 
  },
  onSchoolAtmosphereChange(e) { 
    this.setData({ 
      schoolAtmosphere: this.data.schoolAtmosphereOptions[e.detail.value] 
    }); 
  },
  onInternationalLevelChange(e) { 
    this.setData({ 
      internationalLevel: this.data.internationalLevelOptions[e.detail.value] 
    }); 
  },
  onMajorChange(e) { 
    this.setData({ 
      major: this.data.majorOptions[e.detail.value] 
    }); 
  },
  // 活动类型选择事件
  onResearchTypeChange(e) { 
    this.setData({ 
      researchType: this.data.researchTypeOptions[e.detail.value] 
    }); 
  },
  onVolunteerTypeChange(e) { 
    this.setData({ 
      volunteerType: this.data.volunteerTypeOptions[e.detail.value] 
    }); 
  },
  onInternshipTypeChange(e) { 
    this.setData({ 
      internshipType: this.data.internshipTypeOptions[e.detail.value] 
    }); 
  },
  onArtPracticeTypeChange(e) { 
    this.setData({ 
      artPracticeType: this.data.artPracticeTypeOptions[e.detail.value] 
    }); 
  },
  onFullTimeWorkTypeChange(e) { 
    this.setData({ 
      fullTimeWorkType: this.data.fullTimeWorkTypeOptions[e.detail.value] 
    }); 
  },
  // 提交
  onSubmit() {
    const { gpa, testType, testScore, englishTestType, englishScore, 
            researchExperience, volunteerExperience, internshipExperience, 
            artPractice, fullTimeWork, honors, 
            careerInterest, location, schoolSize, tuition, major, 
            teacherStudentRatio, schoolAtmosphere, internationalLevel, 
            researchType, volunteerType, internshipType, artPracticeType, fullTimeWorkType } = this.data;

    // 验证逻辑已暂时无效化，方便调试
    /*
    let missing = [];
    if (!gpa) missing.push("GPA");
    if (!testType) missing.push("考试类型(SAT/ACT)");
    if (!testScore) missing.push("考试成绩");
    if (!englishTestType) missing.push("英语考试类型");
    if (!englishScore) missing.push("英语成绩");
    if (!careerInterest) missing.push("职业兴趣");
    if (!location) missing.push("学校位置");
    if (!schoolSize) missing.push("学校规模");
    if (!major) missing.push("专业");

    if (missing.length > 0) {
      wx.showModal({ title: "提示", content: "请填写: " + missing.join("、"), showCancel: false });
      return;
    }
    */

    this.setData({ loading: true });

    // 准备发送到后端的数据
    const requestData = {
      academics: {
        gpa,
        sat: testType === 'SAT' ? testScore : null,
        act: testType === 'ACT' ? testScore : null,
        toefl: englishTestType.includes('托福') ? englishScore : null,
        ielts: englishTestType.includes('雅思') ? englishScore : null,
        det: englishTestType.includes('多邻国') ? englishScore : null
      },
      activities: {
        research_months: parseInt(researchExperience) || 0,
        research_type: researchType,
        volunteer_months: parseInt(volunteerExperience) || 0,
        volunteer_type: volunteerType,
        internship_months: parseInt(internshipExperience) || 0,
        internship_type: internshipType,
        art_months: parseInt(artPractice) || 0,
        art_type: artPracticeType,
        full_time_work_months: parseInt(fullTimeWork) || 0,
        full_time_work_type: fullTimeWorkType,
        honors: honors
      },  
      preferences: {
        career_interest: careerInterest,
        location: location,
        size: schoolSize,
        tuition: tuition,
        major: major,
        teacher_student_ratio: teacherStudentRatio,
        school_atmosphere: schoolAtmosphere,
        international_level: internationalLevel
      }
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
        // 重新保存studentProfile以确保数据完整性
        app.globalData.studentProfile = requestData;
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








