<template>
  <div class="publish-page">
    <van-nav-bar :title="isEdit ? '编辑新闻' : '发布新闻'" left-arrow fixed @click-left="router.back()" />

    <main class="publish-content">
      <section class="publish-hero">
        <div>
          <span>NEWSROOM</span>
          <h1>{{ isEdit ? '修改已发布新闻' : '上传一条新新闻' }}</h1>
          <p>{{ isEdit ? '更新标题、正文、分类和封面。' : '填写正文并添加封面，发布后会进入对应频道列表。' }}</p>
        </div>
        <van-icon name="description-o" />
      </section>

      <van-form class="publish-form" @submit="handleSubmit">
        <div class="form-card">
          <label class="field-label">新闻分类</label>
          <select v-model.number="form.categoryId" class="category-select" :disabled="!categories.length">
            <option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </option>
          </select>

          <van-field
            v-model="form.title"
            name="title"
            label="标题"
            maxlength="255"
            placeholder="请输入新闻标题"
            :rules="[{ required: true, message: '请填写新闻标题' }]"
          />

          <van-field
            v-model="form.description"
            name="description"
            label="简介"
            type="textarea"
            rows="2"
            autosize
            maxlength="120"
            show-word-limit
            placeholder="一句话概括新闻重点"
          />

          <van-field
            v-model="form.content"
            name="content"
            label="正文"
            type="textarea"
            rows="8"
            autosize
            :rules="[
              { required: true, message: '请填写新闻正文' },
              { validator: validateContent, message: '新闻正文至少需要 10 个字符' }
            ]"
            placeholder="请输入完整新闻内容"
          />
        </div>

        <div class="form-card">
          <div class="cover-head">
            <label class="field-label">封面图片</label>
            <span>本地上传或填写图片链接</span>
          </div>

          <van-uploader
            v-model="fileList"
            accept="image/*"
            :max-count="1"
            :before-read="beforeReadImage"
            :after-read="afterReadImage"
            @delete="removeImageFile"
          />

          <van-field
            v-model="form.imageUrl"
            name="imageUrl"
            label="图片链接"
            maxlength="255"
            placeholder="可选，支持 https 图片地址"
          />

          <div v-if="previewImage" class="cover-preview">
            <img :src="previewImage" alt="封面预览">
          </div>
        </div>

        <div class="form-card">
          <van-field
            v-model="form.author"
            name="author"
            label="作者"
            placeholder="默认使用当前登录用户名"
          />
        </div>

        <div class="submit-bar">
          <van-button round block type="primary" native-type="submit" :loading="submitting">
            {{ isEdit ? '保存修改' : '发布新闻' }}
          </van-button>
        </div>
      </van-form>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast, showToast } from 'vant'
import { fetchCategories, fetchMyNewsDetail, publishNews, updateNews } from '../services/newsService'
import { useUserStore } from '../store/user'
import { apiConfig } from '../config/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const virtualCategoryNames = new Set(['推荐', '热榜', '关注', '更多'])
const categories = ref([])
const fileList = ref([])
const submitting = ref(false)
const editId = computed(() => Number(route.query.id) || 0)
const isEdit = computed(() => editId.value > 0)

const form = reactive({
  categoryId: 1,
  title: '',
  description: '',
  content: '',
  imageUrl: '',
  imageFile: null,
  author: ''
})

const previewImage = computed(() => {
  if (form.imageFile) return fileList.value[0]?.content || ''
  const imageUrl = form.imageUrl.trim()
  return imageUrl.startsWith('/uploads/') ? `${apiConfig.baseURL}${imageUrl}` : imageUrl
})

const beforeReadImage = (file) => {
  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件')
    return false
  }

  if (file.size > 5 * 1024 * 1024) {
    showToast('封面图片不能超过 5MB')
    return false
  }

  return true
}

const afterReadImage = (item) => {
  form.imageFile = item.file
}

const removeImageFile = () => {
  form.imageFile = null
}

const validateContent = (value) => String(value || '').trim().length >= 10

const getErrorMessage = (error) => {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join('；') || '新闻发布失败'
  }

  return detail || error.response?.data?.message || '新闻发布失败，请稍后再试'
}

const ensureLogin = () => {
  if (userStore.getLoginStatus) return true
  showToast(isEdit.value ? '请先登录后再编辑新闻' : '请先登录后再发布新闻')
  router.push('/login')
  return false
}

const handleSubmit = async () => {
  if (!ensureLogin() || submitting.value) return
  if (!categories.value.length || !form.categoryId) {
    showToast('新闻分类加载失败，请稍后再试')
    return
  }

  submitting.value = true
  try {
    const response = isEdit.value
      ? await updateNews(editId.value, form)
      : await publishNews(form)
    if (response?.code === 200) {
      showSuccessToast(isEdit.value ? '新闻修改成功' : '新闻发布成功')
      const newsId = response.data?.id
      if (newsId) router.replace(`/news/detail/${newsId}`)
      else router.replace('/home')
      return
    }

    showFailToast(response?.message || (isEdit.value ? '新闻修改失败' : '新闻发布失败'))
  } catch (error) {
    console.error(isEdit.value ? '修改新闻失败:' : '发布新闻失败:', error)
    showFailToast(getErrorMessage(error))
  } finally {
    submitting.value = false
  }
}

const loadCategories = async () => {
  const list = await fetchCategories()
  const filtered = list.filter((category) => category.name && !virtualCategoryNames.has(category.name))
  categories.value = filtered
  if (filtered.length && !form.categoryId) {
    form.categoryId = filtered[0].id
  }
}

const loadEditNews = async () => {
  if (!isEdit.value || !ensureLogin()) return

  const detail = await fetchMyNewsDetail(editId.value)
  if (!detail) {
    showToast('新闻不存在或无权编辑')
    router.replace('/my-news')
    return
  }

  form.categoryId = detail.categoryId ?? detail.category_id
  form.title = detail.title || ''
  form.description = detail.description || ''
  form.content = detail.content || ''
  form.imageUrl = detail.image || ''
  form.imageFile = null
  form.author = detail.author || ''
  fileList.value = []
}

onMounted(async () => {
  try {
    await loadCategories()
    await loadEditNews()
  } catch (error) {
    console.error(isEdit.value ? '加载编辑新闻失败:' : '获取新闻分类失败:', error)
    showToast(isEdit.value ? getErrorMessage(error) : '新闻分类加载失败')
  }
})
</script>

<style scoped>
.publish-page {
  min-height: 100vh;
  background: #f6f7f9;
}

:deep(.van-nav-bar) {
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(18px);
}

.publish-content {
  padding: 58px 12px 24px;
}

.publish-hero,
.form-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.04);
}

.publish-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px;
  margin-bottom: 12px;
}

.publish-hero span {
  color: #f04438;
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.publish-hero h1 {
  margin: 7px 0 6px;
  color: #111827;
  font-size: 22px;
  font-weight: 900;
}

.publish-hero p {
  margin: 0;
  color: #8a93a3;
  font-size: 13px;
}

.publish-hero .van-icon {
  color: #f04438;
  font-size: 34px;
}

.form-card {
  margin-bottom: 12px;
  padding: 12px;
  overflow: hidden;
}

.field-label {
  display: block;
  margin: 4px 4px 8px;
  color: #111827;
  font-size: 14px;
  font-weight: 900;
}

.category-select {
  width: 100%;
  height: 44px;
  margin-bottom: 8px;
  padding: 0 12px;
  color: #111827;
  font-size: 14px;
  background: #f7f8fa;
  border: 1px solid #eceff3;
  border-radius: 8px;
  outline: 0;
}

:deep(.van-cell) {
  padding-right: 0;
  padding-left: 0;
}

:deep(.van-field__label) {
  width: 48px;
  color: #111827;
  font-weight: 800;
}

.cover-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.cover-head span {
  color: #9aa3af;
  font-size: 12px;
}

.cover-preview {
  margin-top: 12px;
  overflow: hidden;
  background: #eef2f7;
  border-radius: 8px;
}

.cover-preview img {
  display: block;
  width: 100%;
  max-height: 190px;
  object-fit: cover;
}

.submit-bar {
  position: sticky;
  bottom: 12px;
  z-index: 5;
  padding: 8px 0;
}
</style>
