Page({
  /**
  
  页面的初始数据
  */
  data: {
  // 活动类型选择 - 数组以支持多选
  researchType: [],
  volunteerType: [],
  internshipType: [],
  artPracticeType: [],
  fullTimeWorkType: [],
  
  // 活动类型对应的时长 - 使用对象存储每个类型的时长
  researchExperiences: {},
  volunteerExperiences: {},
  internshipExperiences: {},
  artPractices: {},
  fullTimeWorks: {},
  
  honors: "",
  
  // 活动类型选项
  researchTypeOptions: ["校内科研项目", "校外科研实习", "学术竞赛", "独立研究", "其他"],
  volunteerTypeOptions: ["公益组织", "学校社团", "社区服务", "环保活动", "其他"],
  internshipTypeOptions: ["科技公司", "金融机构", "教育机构", "文创产业", "自主创业/公众号", "其他"],
  artPracticeTypeOptions: ["音乐", "美术", "舞蹈", "戏剧", "数字艺术", "其他"],
  fullTimeWorkTypeOptions: ["科技行业", "金融行业", "教育行业", "医疗行业", "政府机构", "其他"]
  
  },
  
  onLoad: function (options) {
  const app = getApp();
  if (app.globalData.formData && app.globalData.formData.activities) {
  const activities = app.globalData.formData.activities;
  this.setData({
  researchType: activities.researchType || [],
  volunteerType: activities.volunteerType || [],
  internshipType: activities.internshipType || [],
  artPracticeType: activities.artPracticeType || [],
  fullTimeWorkType: activities.fullTimeWorkType || [],
  researchExperiences: activities.researchExperiences || {},
  volunteerExperiences: activities.volunteerExperiences || {},
  internshipExperiences: activities.internshipExperiences || {},
  artPractices: activities.artPractices || {},
  fullTimeWorks: activities.fullTimeWorks || {},
  honors: activities.honors || ""
  });
  }
  },
  
  // 活动类型切换
  onResearchTypeToggle(e) { this.toggleOption('researchType', e.currentTarget.dataset.type); },
  onVolunteerTypeToggle(e) { this.toggleOption('volunteerType', e.currentTarget.dataset.type); },
  onInternshipTypeToggle(e) { this.toggleOption('internshipType', e.currentTarget.dataset.type); },
  onArtPracticeTypeToggle(e) { this.toggleOption('artPracticeType', e.currentTarget.dataset.type); },
  onFullTimeWorkTypeToggle(e) { this.toggleOption('fullTimeWorkType', e.currentTarget.dataset.type); },
  
  toggleOption(field, value) {
  const currentValues = this.data[field];
  let newValues = currentValues.includes(value)
  ? currentValues.filter(item => item !== value)
  : [...currentValues, value];
  this.setData({ [field]: newValues });
  },
  
  // 活动经历输入
  onInputResearchExperience(e) { this.updateExperience('researchExperiences', e); },
  onInputVolunteerExperience(e) { this.updateExperience('volunteerExperiences', e); },
  onInputInternshipExperience(e) { this.updateExperience('internshipExperiences', e); },
  onInputArtPractice(e) { this.updateExperience('artPractices', e); },
  onInputFullTimeWork(e) { this.updateExperience('fullTimeWorks', e); },
  onInputHonors(e) { this.setData({ honors: e.detail.value }); },
  
  updateExperience(field, e) {
  const type = e.currentTarget.dataset.type;
  const experiences = { ...this.data[field] };
  experiences[type] = e.detail.value;
  this.setData({ [field]: experiences });
  },
  
  // 返回上一页
  goBack: function() {
  this.saveData();
  wx.navigateTo({ url: '/pages/standard-score/standard-score' });
  },
  
  // 跳转下一步
  goToNext: function() {
  this.saveData();
  wx.navigateTo({ url: '/pages/school-preference/school-preference' });
  }, 
  
  // 保存数据到全局
  saveData: function() {
  const app = getApp();
  if (!app.globalData.formData) app.globalData.formData = {};
  
  // 原始表单活动数据
  const activitiesData = {
    researchType: this.data.researchType,
    volunteerType: this.data.volunteerType,
    internshipType: this.data.internshipType,
    artPracticeType: this.data.artPracticeType,
    fullTimeWorkType: this.data.fullTimeWorkType,
    researchExperiences: this.data.researchExperiences,
    volunteerExperiences: this.data.volunteerExperiences,
    internshipExperiences: this.data.internshipExperiences,
    artPractices: this.data.artPractices,
    fullTimeWorks: this.data.fullTimeWorks,
    honors: this.data.honors
  };
  
  app.globalData.formData.activities = activitiesData;
  
  // 确保 studentProfile 存在，不覆盖已有学术数据
  if (!app.globalData.studentProfile) app.globalData.studentProfile = {};
  
  // 生成总时长和后端所需格式
  const calculateTotalMonths = (experiences) => {
    return Object.values(experiences).reduce((total, months) => total + (parseInt(months) || 0), 0);
  };
  
  const formattedActivities = {
    research_months: calculateTotalMonths(this.data.researchExperiences),
    research_type: (this.data.researchType || []).join(';') || '',
    research_details: JSON.stringify(this.data.researchExperiences || {}),
    volunteer_months: calculateTotalMonths(this.data.volunteerExperiences),
    volunteer_type: (this.data.volunteerType || []).join(';') || '',
    volunteer_details: JSON.stringify(this.data.volunteerExperiences || {}),
    internship_months: calculateTotalMonths(this.data.internshipExperiences),
    internship_type: (this.data.internshipType || []).join(';') || '',
    internship_details: JSON.stringify(this.data.internshipExperiences || {}),
    art_months: calculateTotalMonths(this.data.artPractices),
    art_type: (this.data.artPracticeType || []).join(';') || '',
    art_details: JSON.stringify(this.data.artPractices || {}),
    full_time_work_months: calculateTotalMonths(this.data.fullTimeWorks),
    full_time_work_type: (this.data.fullTimeWorkType || []).join(';') || '',
    full_time_work_details: JSON.stringify(this.data.fullTimeWorks || {}),
    honors: this.data.honors || ''
  };
  
  // 合并到 studentProfile.activities，不覆盖其他字段
  app.globalData.studentProfile.activities = {
    ...app.globalData.studentProfile.activities,
    ...activitiesData,
    ...formattedActivities
  };
  }
  });