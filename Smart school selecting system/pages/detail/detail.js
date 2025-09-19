Page({
  data: {
    report: '',
    reachSchools: [],
    matchSchools: [],
    safetySchools: [],
  },

  onLoad() {
    const data = wx.getStorageSync('schoolData') || {};
    const initSchools = (arr) => arr.map(s => ({ ...s, showInfo: false }));
    this.setData({
      report: data.report || '',
      reachSchools: initSchools(data.reachSchools || []),
      matchSchools: initSchools(data.matchSchools || []),
      safetySchools: initSchools(data.safetySchools || []),
    });
  },

  toggleSchoolInfo(e) {
    const index = e.currentTarget.dataset.index;
    const level = e.currentTarget.dataset.level;
    const key = `${level}Schools`;
    const schools = this.data[key].map((s, i) => {
      if (i === index) s.showInfo = !s.showInfo;
      return s;
    });
    this.setData({ [key]: schools });
  },

  goBack() {
    wx.navigateBack();
  }
});






