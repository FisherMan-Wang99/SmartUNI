Page({
  data: {
    report: '',
    reachSchools: [],
    matchSchools: [],
    safetySchools: [],
  },

  onLoad() {
    // Retrieve the data from local storage
    const data = wx.getStorageSync('schoolData') || {};
    
    // Check if the new structured data format is available
    if (data.recommendations) {
      this.setData({
        report: data.report || '',
        reachSchools: data.recommendations.reach.schools.map(s => ({ ...s, showInfo: false })),
        matchSchools: data.recommendations.match.schools.map(s => ({ ...s, showInfo: false })),
        safetySchools: data.recommendations.safety.schools.map(s => ({ ...s, showInfo: false })),
      });
    } else {
      // Fallback to the old data format if the new one isn't found
      const initSchools = (arr) => arr.map(s => ({ ...s, showInfo: false }));
      this.setData({
        report: data.report || '',
        reachSchools: initSchools(data.reachSchools || []),
        matchSchools: initSchools(data.matchSchools || []),
        safetySchools: initSchools(data.safetySchools || []),
      });
    }
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






