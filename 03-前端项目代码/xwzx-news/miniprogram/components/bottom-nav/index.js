Component({
  properties: {
    active: {
      type: String,
      value: 'home',
    },
  },

  methods: {
    handleTap(event) {
      const page = event.currentTarget.dataset.page
      const current = this.data.active
      if (page === current) return

      const routes = {
        home: '/pages/home/home',
        ai: '/pages/ai-chat/ai-chat',
        my: '/pages/my/my',
      }

      wx.reLaunch({
        url: routes[page] || routes.home,
      })
    },
  },
})
