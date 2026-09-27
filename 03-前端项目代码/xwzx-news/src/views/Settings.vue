<template>
  <div class="settings-container">
    <van-nav-bar
      :title="$t('settings.title')"
      left-arrow
      @click-left="onClickLeft"
    />
    
    <div class="settings-list">
      <van-cell-group inset :title="$t('settings.personalization')">
        <van-cell :title="$t('settings.themeCustomization')" is-link @click="showThemePopup = true" />
        <van-cell :title="$t('settings.languageSettings')" is-link @click="showLanguagePopup = true" />
      </van-cell-group>
      
      <van-cell-group inset :title="$t('settings.account')">
        <van-cell :title="$t('settings.privacySettings')" is-link />
        <van-cell :title="$t('settings.notificationSettings')" is-link />
        <van-cell :title="$t('settings.aboutUs')" is-link />
      </van-cell-group>

      <van-cell-group inset title="新闻同步">
        <van-cell title="同步状态" :value="syncStatusText" />
        <van-cell title="最近结果" :label="syncResultText" />
        <van-cell title="最后同步" :value="lastSyncTimeText" />
        <van-cell
          title="刷新状态"
          is-link
          :value="syncLoading ? '刷新中...' : ''"
          @click="loadSyncStatus"
        />
      </van-cell-group>
    </div>
    
    <!-- 主题选择弹出层 -->
    <van-popup
      v-model:show="showThemePopup"
      position="bottom"
      round
      :style="{ height: '40%' }"
    >
      <div class="popup-title">{{ $t('settings.selectTheme') }}</div>
      <div class="theme-list">
        <div 
          v-for="theme in themeList" 
          :key="theme.id" 
          class="theme-item"
          :class="{ active: currentTheme === theme.id }"
          @click="changeTheme(theme.id)"
        >
          <div class="theme-color" :style="{ backgroundColor: theme.primaryColor }"></div>
          <div class="theme-name">{{ theme.name }}</div>
        </div>
      </div>
    </van-popup>
    
    <!-- 语言选择弹出层 -->
    <van-popup
      v-model:show="showLanguagePopup"
      position="bottom"
      round
      :style="{ height: '40%' }"
    >
      <div class="popup-title">{{ $t('settings.selectLanguage') }}</div>
      <van-radio-group v-model="currentLanguage">
        <van-cell-group inset>
          <van-cell 
            v-for="lang in languageOptions" 
            :key="lang.value" 
            :title="lang.label" 
            clickable 
            @click="currentLanguage = lang.value"
            :class="{ 'language-active': currentLanguage === lang.value }"
          >
            <template #right-icon>
              <van-radio :name="lang.value" />
            </template>
          </van-cell>
        </van-cell-group>
      </van-radio-group>
      <div class="popup-footer">
        <van-button type="primary" block @click="changeLanguage">{{ $t('common.confirm') }}</van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { showToast } from 'vant';
import { useThemeStore } from '../store/theme';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '../store/language';
import { fetchSyncStatus } from '../services/newsService';

const router = useRouter();
const themeStore = useThemeStore();
const languageStore = useLanguageStore();
const { t, locale } = useI18n();

// 返回上一页
const onClickLeft = () => {
  router.back();
};

// 主题相关
const showThemePopup = ref(false);
const themeList = computed(() => themeStore.getAllThemes);
const currentTheme = computed(() => themeStore.getCurrentTheme);

// 切换主题
const changeTheme = (themeId) => {
  themeStore.setTheme(themeId);
  showToast(t('settings.themeChanged'));
  showThemePopup.value = false;
};

// 语言相关
const showLanguagePopup = ref(false);
const currentLanguage = ref(languageStore.getCurrentLanguage);
const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' }
];

const syncLoading = ref(false);
const syncStatus = ref(null);

const formatDateTime = (value) => {
  if (!value) return '暂无';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const syncStatusText = computed(() => {
  if (!syncStatus.value) return '未获取';
  return syncStatus.value.running ? '同步中' : '空闲';
});

const lastSyncTimeText = computed(() => {
  return formatDateTime(syncStatus.value?.last_finished_at);
});

const syncResultText = computed(() => {
  const result = syncStatus.value?.last_result;
  const error = syncStatus.value?.last_error;
  if (error) return `失败：${error}`;
  if (!result) return '暂无同步记录';
  return `来源 ${result.provider}，抓取 ${result.fetched} 条，新增 ${result.inserted} 条，更新 ${result.updated} 条`;
});

const loadSyncStatus = async () => {
  if (syncLoading.value) return;
  syncLoading.value = true;
  try {
    syncStatus.value = await fetchSyncStatus();
  } catch (error) {
    showToast('同步状态获取失败');
  } finally {
    syncLoading.value = false;
  }
};

// 切换语言
const changeLanguage = () => {
  languageStore.setLanguage(currentLanguage.value);
  locale.value = currentLanguage.value;
  showLanguagePopup.value = false;
  showToast(t('settings.languageChanged'));
  // 强制刷新页面以应用语言更改
  window.location.reload();
};

onMounted(loadSyncStatus);
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background-color: var(--background-color);
  color: var(--text-color);
  padding-top: 46px;
  padding-bottom: 20px;
}

.settings-list {
  margin-top: 20px;
}

.settings-list :deep(.van-cell-group) {
  margin-bottom: 12px;
}

.popup-title {
  text-align: center;
  padding: 16px;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #eee;
}

.theme-list {
  display: flex;
  flex-wrap: wrap;
  padding: 16px;
}

.theme-item {
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
  cursor: pointer;
}

.theme-color {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-bottom: 8px;
  border: 2px solid transparent;
}

.theme-item.active .theme-color {
  border-color: #1989fa;
}

.theme-name {
  font-size: 12px;
}

.popup-footer {
  padding: 16px;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}

.language-active {
  background-color: #f5f5f5;
}
</style>
