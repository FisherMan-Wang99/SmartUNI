// pages/index/index.js
Page({
  onLoad: function(options) {
    // 页面加载时的初始化逻辑
    // 初始化所有职业兴趣选项为已选中状态，并设置默认排序
    const allCareerInterests = this.data.careerInterestOptions.map((item, index) => ({
      id: item.id,
      name: item.name,
      rank: index + 1
    }));
    
    // 创建id到排序号的映射
    const idToRankMap = {};
    allCareerInterests.forEach(item => {
      idToRankMap[item.id] = item.rank;
    });
    
    this.setData({
      selectedCareerInterests: allCareerInterests,
      sortedCareerInterests: allCareerInterests,
      idToRankMap: idToRankMap,
      careerInterestOptions: this.data.careerInterestOptions.map(item => ({...item, checked: true}))
    });
  },

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
    
    // 活动类型选择 - 改为数组以支持多选
    researchType: [], // 课外科研类型（多选）
    volunteerType: [], // 志愿者活动类型（多选）
    internshipType: [], // 兼职、实习类型（多选）
    artPracticeType: [], // 艺术实践类型（多选）
    fullTimeWorkType: [], // 全职工作类型（多选）
    
    // 活动类型对应的时长 - 使用对象存储每个类型的时长
    researchExperiences: {}, // 课外科研时长 {type: months}
    volunteerExperiences: {}, // 志愿者活动时长 {type: months}
    internshipExperiences: {}, // 兼职、实习时长 {type: months}
    artPractices: {}, // 艺术实践时长 {type: months}
    fullTimeWorks: {}, // 全职工作时长 {type: months}
    
    // 学校偏好
    careerInterest: [], // 职业兴趣改为数组，存储排序后的结果
    location: 2, // 位置（0-4，默认2-无所谓）
    schoolSize: 2, // 规模（0-4，默认2-正常）
    tuition: 150000, // 学费（默认值）
    major: "", // 专业
    teacherStudentRatio: 2, // 师生关系（0-1，默认0-更关心）
    schoolAtmosphere: 1, // 学校氛围（0-2，默认1-Neutral）
    internationalLevel: 2, // 国际化程度（0-1，默认0-高）
    
    loading: false,
    noData: false,
  
    // 职业兴趣排序相关
    careerInterestOptions: [
      { id: 1, name: "做科研、进大学、企业科研部门当老师、研发人员", checked: false },
      { id: 2, name: "毕业后进市场找工作", checked: false },
      { id: 3, name: "创业", checked: false },
      { id: 4, name: "进入政府机构或非营利组织", checked: false },
      { id: 5, name: "继续深造获取更高学位", checked: false }
    ],
    selectedCareerInterests: [], // 存储选中的兴趣项
    sortedCareerInterests: [], // 存储排序后的兴趣项
    dragSrcIndex: -1, // 拖拽源索引
    dragTargetIndex: -1, // 拖拽目标索引
    idToRankMap: {}, // 映射id到排序号
    isDragging: -1, // 当前正在拖动的项目索引
    dragY: 0, // 拖拽元素的Y轴偏移量
    
    // 其他下拉选项
    locationOptions: ["大城市", "普通城市", "无所谓", "边郊", "乡村"],
    schoolSizeOptions: ["小（<5000）", "偏小（5000+）", "正常（10000+）", "偏大（20000+）", "大（50000+）"],
    teacherStudentRatioOptions: ["极度关心", "比较关心", "一般", "比较自主", "极度自主"],
    schoolAtmosphereOptions: ["Party School", "Neutral", "Nerdy School"],
    internationalLevelOptions: ["非常高", "比较高", "一般", "比较低", "非常低"],
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
  
  // 活动经历输入事件 - 修改为处理具体类型的时长
  onInputResearchExperience(e) { 
    const type = e.currentTarget.dataset.type;
    const experiences = {...this.data.researchExperiences};
    experiences[type] = e.detail.value;
    this.setData({ researchExperiences: experiences }); 
  },
  onInputVolunteerExperience(e) { 
    const type = e.currentTarget.dataset.type;
    const experiences = {...this.data.volunteerExperiences};
    experiences[type] = e.detail.value;
    this.setData({ volunteerExperiences: experiences }); 
  },
  onInputInternshipExperience(e) { 
    const type = e.currentTarget.dataset.type;
    const experiences = {...this.data.internshipExperiences};
    experiences[type] = e.detail.value;
    this.setData({ internshipExperiences: experiences }); 
  },
  onInputArtPractice(e) { 
    const type = e.currentTarget.dataset.type;
    const experiences = {...this.data.artPractices};
    experiences[type] = e.detail.value;
    this.setData({ artPractices: experiences }); 
  },
  onInputFullTimeWork(e) { 
    const type = e.currentTarget.dataset.type;
    const experiences = {...this.data.fullTimeWorks};
    experiences[type] = e.detail.value;
    this.setData({ fullTimeWorks: experiences }); 
  },
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
  
  // 职业兴趣排序相关方法 - 移除选择功能，所有选项默认可排序
  onCareerInterestToggle(e) { 
    // 保留该方法以避免绑定错误，但不执行任何操作
    // 所有选项默认都在排序列表中
  },
  
  // 开始拖动
  onDragStart(e) {
    this.setData({
      dragSrcIndex: e.currentTarget.dataset.index,
      dragTargetIndex: -1,
      isDragging: e.currentTarget.dataset.index, // 记录正在拖动的索引
      dragY: 0 // 重置偏移量
    });
    
    // 记录触摸起始位置
    this.touchStartY = e.touches[0].clientY;
    // 记录拖动元素的原始位置
    this.dragStartIndex = e.currentTarget.dataset.index;
  },
  
  // 拖动过程中
  onDragMove(e) {
    if (this.data.dragSrcIndex === -1) return;
    
    const currentY = e.touches[0].clientY;
    const deltaY = currentY - this.touchStartY;
    const itemHeight = 120; // 大约每个选项的高度（单位：rpx）
    const list = this.data.selectedCareerInterests;
    
    // 更新拖动元素的偏移量
    this.setData({
      dragY: deltaY
    });
    
    // 计算应该移动到的位置
    if (deltaY > itemHeight / 3 && this.data.dragSrcIndex < list.length - 1) {
      // 向下移动（降低阈值提高灵敏度）
      this.swapItems(this.data.dragSrcIndex, this.data.dragSrcIndex + 1);
      this.touchStartY = currentY;
      this.setData({ dragY: 0 });
    } else if (deltaY < -itemHeight / 3 && this.data.dragSrcIndex > 0) {
      // 向上移动（降低阈值提高灵敏度）
      this.swapItems(this.data.dragSrcIndex, this.data.dragSrcIndex - 1);
      this.touchStartY = currentY;
      this.setData({ dragY: 0 });
    }
  },
   
  // 拖动结束
  onDragEnd(e) {
    // 先设置偏移量为0，触发归位动画
    this.setData({
      dragY: 0
    }, () => {
      // 动画结束后重置状态
      setTimeout(() => {
        this.setData({
          dragSrcIndex: -1,
          dragTargetIndex: -1,
          isDragging: -1 // 重置拖动状态
        });
      }, 300); // 等待动画完成
    });
  },
  
  // 交换列表中的两个元素
  swapItems(fromIndex, toIndex) {
    const updatedList = [...this.data.selectedCareerInterests];
    const temp = updatedList[fromIndex];
    updatedList[fromIndex] = updatedList[toIndex];
    updatedList[toIndex] = temp;
    
    // 更新所有项目的排序号
    for (let i = 0; i < updatedList.length; i++) {
      updatedList[i].rank = i + 1;
    }
    
    // 更新id到排序号的映射
    const idToRankMap = {};
    updatedList.forEach(item => {
      idToRankMap[item.id] = item.rank;
    });
    
    this.setData({
      selectedCareerInterests: updatedList,
      sortedCareerInterests: updatedList, // 更新排序结果
      dragSrcIndex: toIndex, // 更新拖拽源索引
      idToRankMap: idToRankMap
    });
    
    // 提供视觉反馈
    wx.vibrateShort();
  },
  // 滑动条处理函数
  onLocationChange(e) { 
    this.setData({ 
      location: e.detail.value 
    }); 
  },    
  onSchoolSizeChange(e) { 
    this.setData({ 
      schoolSize: e.detail.value 
    }); 
  },
  onTeacherStudentRatioChange(e) { 
    this.setData({ 
      teacherStudentRatio: e.detail.value 
    }); 
  },
  onSchoolAtmosphereChange(e) { 
    this.setData({ 
      schoolAtmosphere: e.detail.value 
    }); 
  },
  onInternationalLevelChange(e) { 
    this.setData({ 
      internationalLevel: e.detail.value 
    }); 
  },
  onMajorChange(e) { 
    this.setData({ 
      major: this.data.majorOptions[e.detail.value] 
    }); 
  },
  // 活动类型选择事件 - 修改为支持多选
  onResearchTypeToggle(e) { 
    const type = e.currentTarget.dataset.type;
    const currentTypes = [...this.data.researchType];
    const index = currentTypes.indexOf(type);
    
    if (index === -1) {
      // 添加类型
      currentTypes.push(type);
      // 初始化对应时长为""
      const experiences = {...this.data.researchExperiences};
      experiences[type] = "";
      this.setData({ 
        researchType: currentTypes,
        researchExperiences: experiences
      });
    } else {
      // 移除类型
      currentTypes.splice(index, 1);
      // 删除对应时长
      const experiences = {...this.data.researchExperiences};
      delete experiences[type];
      this.setData({ 
        researchType: currentTypes,
        researchExperiences: experiences
      });
    }
  },
  onVolunteerTypeToggle(e) { 
    const type = e.currentTarget.dataset.type;
    const currentTypes = [...this.data.volunteerType];
    const index = currentTypes.indexOf(type);
    
    if (index === -1) {
      // 添加类型
      currentTypes.push(type);
      // 初始化对应时长为""
      const experiences = {...this.data.volunteerExperiences};
      experiences[type] = "";
      this.setData({ 
        volunteerType: currentTypes,
        volunteerExperiences: experiences
      });
    } else {
      // 移除类型
      currentTypes.splice(index, 1);
      // 删除对应时长
      const experiences = {...this.data.volunteerExperiences};
      delete experiences[type];
      this.setData({ 
        volunteerType: currentTypes,
        volunteerExperiences: experiences
      });
    }
  },
  onInternshipTypeToggle(e) { 
    const type = e.currentTarget.dataset.type;
    const currentTypes = [...this.data.internshipType];
    const index = currentTypes.indexOf(type);
    
    if (index === -1) {
      // 添加类型
      currentTypes.push(type);
      // 初始化对应时长为""
      const experiences = {...this.data.internshipExperiences};
      experiences[type] = "";
      this.setData({ 
        internshipType: currentTypes,
        internshipExperiences: experiences
      });
    } else {
      // 移除类型
      currentTypes.splice(index, 1);
      // 删除对应时长
      const experiences = {...this.data.internshipExperiences};
      delete experiences[type];
      this.setData({ 
        internshipType: currentTypes,
        internshipExperiences: experiences
      });
    }
  },
  onArtPracticeTypeToggle(e) { 
    const type = e.currentTarget.dataset.type;
    const currentTypes = [...this.data.artPracticeType];
    const index = currentTypes.indexOf(type);
    
    if (index === -1) {
      // 添加类型
      currentTypes.push(type);
      // 初始化对应时长为""
      const experiences = {...this.data.artPractices};
      experiences[type] = "";
      this.setData({ 
        artPracticeType: currentTypes,
        artPractices: experiences
      });
    } else {
      // 移除类型
      currentTypes.splice(index, 1);
      // 删除对应时长
      const experiences = {...this.data.artPractices};
      delete experiences[type];
      this.setData({ 
        artPracticeType: currentTypes,
        artPractices: experiences
      });
    }
  },
  onFullTimeWorkTypeToggle(e) { 
    const type = e.currentTarget.dataset.type;
    const currentTypes = [...this.data.fullTimeWorkType];
    const index = currentTypes.indexOf(type);
    
    if (index === -1) {
      // 添加类型
      currentTypes.push(type);
      // 初始化对应时长为""
      const experiences = {...this.data.fullTimeWorks};
      experiences[type] = "";
      this.setData({ 
        fullTimeWorkType: currentTypes,
        fullTimeWorks: experiences
      });
    } else {
      // 移除类型
      currentTypes.splice(index, 1);
      // 删除对应时长
      const experiences = {...this.data.fullTimeWorks};
      delete experiences[type];
      this.setData({ 
        fullTimeWorkType: currentTypes,
        fullTimeWorks: experiences
      });
    }
  },
  // 提交
  onSubmit() {
    const { gpa, testType, testScore, englishTestType, englishScore, 
            honors, 
            location, schoolSize, tuition, major, 
            teacherStudentRatio, schoolAtmosphere, internationalLevel, 
            researchType, volunteerType, internshipType, artPracticeType, fullTimeWorkType,
            researchExperiences, volunteerExperiences, internshipExperiences,
            artPractices, fullTimeWorks } = this.data;
    
    // 处理职业兴趣数据 - 使用所有选项的完整列表
    const careerInterest = this.data.careerInterestOptions.map(item => item.name).join(';');
      
    // 计算各活动类型的总时长
    const calculateTotalMonths = (experiences) => {
      return Object.values(experiences).reduce((total, months) => {
        return total + (parseInt(months) || 0);
      }, 0);
    };
    
    // 计算各类活动的总时长
    const researchExperience = calculateTotalMonths(researchExperiences);
    const volunteerExperience = calculateTotalMonths(volunteerExperiences);
    const internshipExperience = calculateTotalMonths(internshipExperiences);
    const artPractice = calculateTotalMonths(artPractices);
    const fullTimeWork = calculateTotalMonths(fullTimeWorks);

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
        sat: testType.toLowerCase() === 'sat' ? testScore : null,
        act: testType.toLowerCase() === 'act' ? testScore : null,
        toefl: englishTestType.toLowerCase().includes('托福') || englishTestType.toLowerCase().includes('toefl') ? englishScore : null,
        ielts: englishTestType.toLowerCase().includes('雅思') || englishTestType.toLowerCase().includes('ielts') ? englishScore : null,
        det: englishTestType.toLowerCase().includes('多邻国') || englishTestType.toLowerCase().includes('det') ? englishScore : null
      },
      activities: {
        // 总时长（转换为数字类型）
        research_months: parseInt(researchExperience) || 0,
        research_type: researchType.join(';') || '', // 多选类型用分号分隔
        research_details: JSON.stringify(researchExperiences), // 保存详细的类型-时长对应关系
        volunteer_months: parseInt(volunteerExperience) || 0,
        volunteer_type: volunteerType.join(';') || '',
        volunteer_details: JSON.stringify(volunteerExperiences),
        internship_months: parseInt(internshipExperience) || 0,
        internship_type: internshipType.join(';') || '',
        internship_details: JSON.stringify(internshipExperiences),
        art_months: parseInt(artPractice) || 0,
        art_type: artPracticeType.join(';') || '',
        art_details: JSON.stringify(artPractices),
        full_time_work_months: parseInt(fullTimeWork) || 0,
        full_time_work_type: fullTimeWorkType.join(';') || '',
        full_time_work_details: JSON.stringify(fullTimeWorks),
        honors: honors || ''
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
 
        // 跳转到加载页面，而不是直接跳转到详情页
        wx.navigateTo({ url: '/pages/loading/loading' });
      },
      fail: (err) => {
        console.error("请求失败:", err);
        this.setData({ loading: false });
        wx.showToast({ title: "请求失败，请检查后端地址或网络", icon: "none" });
      }
    });
  }
});








