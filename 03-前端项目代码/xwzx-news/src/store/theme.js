import { defineStore } from 'pinia';

export const useThemeStore = defineStore('theme', {
  state: () => ({
    currentTheme: localStorage.getItem('theme') || 'light', // 默认浅色主题
    themes: {
      light: {
        name: '浅色模式',
        backgroundColor: '#f4f7fb',
        textColor: '#263238',
        primaryColor: '#1989fa',
        secondaryColor: '#eef5ff',
        textColorLight: '#5d6872',
        textColorLighter: '#8a96a3',
        borderColor: '#e8edf3',
        cardColor: '#ffffff',
        navColor: 'rgba(255, 255, 255, 0.94)',
        shadowColor: 'rgba(28, 58, 92, 0.1)',
        pageGradient: 'linear-gradient(180deg, #eef6ff 0%, #f6f8fb 38%, #f4f7fb 100%)'
      },
      dark: {
        name: '深色模式',
        backgroundColor: '#10151d',
        textColor: '#f3f7fb',
        primaryColor: '#6aa8ff',
        secondaryColor: '#1b2633',
        textColorLight: '#c0cad6',
        textColorLighter: '#8492a3',
        borderColor: '#263445',
        cardColor: '#17202b',
        navColor: 'rgba(16, 21, 29, 0.94)',
        shadowColor: 'rgba(0, 0, 0, 0.28)',
        pageGradient: 'linear-gradient(180deg, #132033 0%, #10151d 42%, #0e131a 100%)'
      },
      blue: {
        name: '蓝色主题',
        backgroundColor: '#eaf6ff',
        textColor: '#17324d',
        primaryColor: '#1890ff',
        secondaryColor: '#d9efff',
        textColorLight: '#4d6985',
        textColorLighter: '#7c91a7',
        borderColor: '#cfe6fa',
        cardColor: '#ffffff',
        navColor: 'rgba(245, 251, 255, 0.94)',
        shadowColor: 'rgba(24, 144, 255, 0.13)',
        pageGradient: 'linear-gradient(180deg, #dff2ff 0%, #eef9ff 44%, #eaf6ff 100%)'
      },
      green: {
        name: '绿色主题',
        backgroundColor: '#f2faef',
        textColor: '#233821',
        primaryColor: '#52c41a',
        secondaryColor: '#e6f7dc',
        textColorLight: '#526b4d',
        textColorLighter: '#7e9278',
        borderColor: '#d8ebd0',
        cardColor: '#ffffff',
        navColor: 'rgba(250, 255, 247, 0.94)',
        shadowColor: 'rgba(82, 196, 26, 0.12)',
        pageGradient: 'linear-gradient(180deg, #e4f8dd 0%, #f5fbf2 44%, #f2faef 100%)'
      }
    }
  }),
  
  getters: {
    getCurrentTheme: (state) => state.currentTheme,
    getThemeConfig: (state) => state.themes[state.currentTheme],
    getAllThemes: (state) => Object.keys(state.themes).map(key => ({
      id: key,
      name: state.themes[key].name,
      primaryColor: state.themes[key].primaryColor
    }))
  },
  
  actions: {
    setTheme(themeName) {
      if (this.themes[themeName]) {
        this.currentTheme = themeName;
        localStorage.setItem('theme', themeName);
        this.applyTheme();
      }
    },
    
    applyTheme() {
      const theme = this.themes[this.currentTheme];
      document.documentElement.style.setProperty('--background-color', theme.backgroundColor);
      document.documentElement.style.setProperty('--text-color', theme.textColor);
      document.documentElement.style.setProperty('--primary-color', theme.primaryColor);
      document.documentElement.style.setProperty('--primary-color-soft', `${theme.primaryColor}1a`);
      document.documentElement.style.setProperty('--secondary-color', theme.secondaryColor);
      document.documentElement.style.setProperty('--text-color-light', theme.textColorLight);
      document.documentElement.style.setProperty('--text-color-lighter', theme.textColorLighter);
      document.documentElement.style.setProperty('--border-color', theme.borderColor);
      document.documentElement.style.setProperty('--card-color', theme.cardColor);
      document.documentElement.style.setProperty('--nav-color', theme.navColor);
      document.documentElement.style.setProperty('--shadow-color', theme.shadowColor);
      document.documentElement.style.setProperty('--page-gradient', theme.pageGradient);
    },
    
    initTheme() {
      this.applyTheme();
    }
  }
});