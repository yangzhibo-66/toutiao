Component({
  properties: {
    item: {
      type: Object,
      value: {},
    },
    mode: {
      type: String,
      value: 'default',
    },
  },

  methods: {
    handleTap() {
      this.triggerEvent('tapcard', {
        id: this.data.item.id,
      })
    },
  },
})
