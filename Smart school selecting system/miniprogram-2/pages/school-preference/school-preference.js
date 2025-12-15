Page({

  data: {
    // 学校偏好
    location: 2,
    schoolSize: 2,
    tuition: 150000,
    major: "",
    teacherStudentRatio: 2,
    schoolAtmosphere: 1,
    internationalLevel: 2,

    // 职业兴趣排序
    careerInterestOptions: [
      { id: 1, name: "做科研、进大学、企业科研部门当老师、研发人员" },
      { id: 2, name: "毕业后进市场找工作" },
      { id: 3, name: "创业" },
      { id: 4, name: "进入政府机构或非营利组织" },
      { id: 5, name: "继续深造获取更高学位" }
    ],
    selectedCareerInterests: [],
    sortedCareerInterests: [],
    idToRankMap: {},
    dragSrcIndex: -1,
    isDragging: -1,
    dragY: 0,
    touchStartY: 0,

    // 选项列表
    locationOptions: ["大城市", "普通城市", "无所谓", "边郊", "乡村"],
    schoolSizeOptions: ["小（<5000）", "偏小（5000+）", "正常（10000+）", "偏大（20000+）", "大（50000+）"],
    teacherStudentRatioOptions: ["极度关心", "比较关心", "一般", "比较自主", "极度自主"],
    schoolAtmosphereOptions: ["Party", "中性", "Nerdy"],
    internationalLevelOptions: ["非常高", "比较高", "一般", "比较低", "非常低"],
    majorOptions: ["计算机科学", "工程学", "商业/金融", "艺术/电影", "生物学", "心理学"]
  },

  onLoad() {
    const initialInterests = this.data.careerInterestOptions.map((item, index) => ({
      id: item.id,
      name: item.name,
      rank: index + 1
    }));

    const idToRank = {};
    initialInterests.forEach(i => idToRank[i.id] = i.rank);

    this.setData({
      selectedCareerInterests: initialInterests,
      sortedCareerInterests: initialInterests,
      idToRankMap: idToRank
    });

    // 加载历史数据（不会加载 academic）
    const app = getApp();
    const sp = app.globalData.formData?.schoolPreference;
    if (sp) {
      this.setData({
        location: sp.location ?? 2,
        schoolSize: sp.schoolSize ?? 2,
        tuition: sp.tuition ?? 150000,
        major: sp.major ?? "",
        teacherStudentRatio: sp.teacherStudentRatio ?? 2,
        schoolAtmosphere: sp.schoolAtmosphere ?? 1,
        internationalLevel: sp.internationalLevel ?? 2,
        selectedCareerInterests: sp.selectedCareerInterests || initialInterests,
        sortedCareerInterests: sp.sortedCareerInterests || initialInterests,
        idToRankMap: sp.idToRankMap || idToRank
      });
    }
  },

  // 选项变化
  onLocationChange(e) { this.setData({ location: e.detail.value }); },
  onSchoolSizeChange(e) { this.setData({ schoolSize: e.detail.value }); },
  onTuitionChange(e) { this.setData({ tuition: e.detail.value }); },
  onTeacherStudentRatioChange(e) { this.setData({ teacherStudentRatio: e.detail.value }); },
  onSchoolAtmosphereChange(e) { this.setData({ schoolAtmosphere: e.detail.value }); },
  onInternationalLevelChange(e) { this.setData({ internationalLevel: e.detail.value }); },
  onMajorChange(e) { this.setData({ major: this.data.majorOptions[e.detail.value] }); },

  // 拖拽排序
  onDragStart(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ dragSrcIndex: index, isDragging: index, dragY: 0 });
    this.touchStartY = e.touches[0].clientY;
  },

  onDragMove(e) {
    if (this.data.dragSrcIndex === -1) return;
    const currentY = e.touches[0].clientY;
    const deltaY = currentY - this.touchStartY;
    const itemHeight = 120;

    this.setData({ dragY: deltaY });

    const list = this.data.selectedCareerInterests;

    if (deltaY > itemHeight / 3 && this.data.dragSrcIndex < list.length - 1) {
      this.swapItems(this.data.dragSrcIndex, this.data.dragSrcIndex + 1);
      this.touchStartY = currentY;
      this.setData({ dragY: 0 });
    } else if (deltaY < -itemHeight / 3 && this.data.dragSrcIndex > 0) {
      this.swapItems(this.data.dragSrcIndex, this.data.dragSrcIndex - 1);
      this.touchStartY = currentY;
      this.setData({ dragY: 0 });
    }
  },

  onDragEnd() {
    const sortedList = this.data.selectedCareerInterests.map((item, index) => ({
      ...item,
      rank: index + 1
    }));
    const idToRankMap = {};
    sortedList.forEach(i => idToRankMap[i.id] = i.rank);

    this.setData({
      dragSrcIndex: -1,
      isDragging: -1,
      dragY: 0,
      selectedCareerInterests: sortedList,
      sortedCareerInterests: sortedList,
      idToRankMap
    });
  },

  swapItems(from, to) {
    const list = [...this.data.selectedCareerInterests];
    [list[from], list[to]] = [list[to], list[from]];
    this.setData({ selectedCareerInterests: list, dragSrcIndex: to });
  },

  // 保存当前页面数据（不会动 academic）
  saveData() {
    const app = getApp();
    if (!app.globalData.formData) app.globalData.formData = {};

    app.globalData.formData.schoolPreference = {
      location: this.data.location,
      schoolSize: this.data.schoolSize,
      tuition: this.data.tuition,
      major: this.data.major,
      teacherStudentRatio: this.data.teacherStudentRatio,
      schoolAtmosphere: this.data.schoolAtmosphere,
      internationalLevel: this.data.internationalLevel,
      selectedCareerInterests: this.data.selectedCareerInterests,
      sortedCareerInterests: this.data.sortedCareerInterests,
      idToRankMap: this.data.idToRankMap
    };
  },

  // 只更新 preferences，不创建 academics！不覆盖成绩！
  buildRequestData() {
    const app = getApp();
    const oldProfile = app.globalData.studentProfile || {};

    const preferences = {
      career_interest: this.data.selectedCareerInterests.map(c => c.name).join(";"),
      location: this.data.location,
      size: this.data.schoolSize,
      tuition: this.data.tuition,
      major: this.data.major,
      teacher_student_ratio: this.data.teacherStudentRatio,
      school_atmosphere: this.data.schoolAtmosphere,
      international_level: this.data.internationalLevel
    };

    app.globalData.studentProfile = {
      ...oldProfile,
      preferences
    };
  },

  // 返回上一页
  goBack() {
    this.saveData();
    wx.navigateTo({ url: "/pages/activities/activities" });
  },

  // 跳转结果
  onSubmit() {
    this.saveData();
    this.buildRequestData();
    wx.navigateTo({ url: "/pages/loading/loading" });
  },

  viewDetailedResult() {
    this.saveData();
    this.buildRequestData();
    wx.navigateTo({ url: "/pages/loading/loading?reportType=detailed" });
  },

  viewQuickResult() {
    this.saveData();
    this.buildRequestData();
    wx.navigateTo({ url: "/pages/loading/loading?reportType=quick" });
  },

  viewVisualResult() {
    this.saveData();
    this.buildRequestData();
    wx.navigateTo({ url: "/pages/loading/loading?reportType=visual" });
  }
});
