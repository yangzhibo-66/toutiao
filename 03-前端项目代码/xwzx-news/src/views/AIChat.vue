<template>
  <div class="ai-chat-container">
    <van-nav-bar title="AI问答" fixed />
    
    <div class="chat-content">
      <div class="chat-hero">
        <span>AI NEWS ASSISTANT</span>
        <strong>问新闻、摘要、观点</strong>
        <p>把热点拆开讲清楚，也可以帮你整理文章重点。</p>
      </div>

      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content">
            <div v-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else v-html="formatMessage(message.content)"></div>
          </div>
        </div>
      </div>
      
      <div class="input-container">
        <van-field
          v-model="userInput"
          rows="1"
          autosize
          type="textarea"
          placeholder="请输入问题..."
          class="chat-input"
          @keypress.enter.prevent="sendMessage"
        />
        <van-button 
          type="primary" 
          class="send-button" 
          :disabled="isLoading || !userInput.trim()" 
          @click="sendMessage"
        >
          发送
        </van-button>
      </div>
    </div>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import TabBar from '../components/TabBar.vue';
import { showToast } from 'vant';
import * as marked from 'marked';
import DOMPurify from 'dompurify';
import { aiChatConfig } from '../config/api';

// 聊天消息
const messages = ref([
  { role: 'assistant', content: '你好！我是AI助手，有什么可以帮助你的吗？' }
]);
const userInput = ref('');
const messagesContainer = ref(null);
const isLoading = ref(false);

// 从配置文件获取API设置
const apiEndpoint = ref(aiChatConfig.apiEndpoint);
const apiKey = ref(aiChatConfig.apiKey);
const model = ref(aiChatConfig.model);

// 格式化消息内容（支持Markdown）
const formatMessage = (content) => {
  if (!content) return '';
  // 使用marked解析Markdown，并用DOMPurify清理HTML
  return DOMPurify.sanitize(marked.parse(content));
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;
  
  // 检查API设置
  if (!apiKey.value || apiKey.value === 'your-api-key-here') {
    showToast('API Key未配置，请联系管理员');
    return;
  }
  
  // 添加用户消息
  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  
  // 添加AI消息占位
  messages.value.push({ role: 'assistant', content: '' });
  
  // 滚动到底部
  await nextTick();
  scrollToBottom();
  
  // 发送请求
  isLoading.value = true;
  try {
    await fetchAIResponse(userMessage);
  } catch (error) {
    console.error('Error fetching AI response:', error);
    // 更新最后一条消息为错误信息
    messages.value[messages.value.length - 1].content = `发生错误: ${error.message || '请检查网络连接和API设置'}`;
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 获取AI响应（使用SSE）
const fetchAIResponse = async (userMessage) => {
  const allMessages = messages.value
    .slice(0, -1) // 排除最后一个空的assistant消息
    .map(msg => ({ role: msg.role, content: msg.content }));
  
  try {
    const response = await fetch(apiEndpoint.value, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey.value}`,
        'X-DashScope-SSE': 'enable' // 添加阿里云DashScope所需的SSE头
      },
      body: JSON.stringify({
        model: model.value,
        messages: allMessages,
        stream: true
      })
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
    }
    
    // 处理SSE流
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let aiResponse = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') continue;
        
        try {
          const json = JSON.parse(data);
          // 适配阿里云DashScope的返回格式
          const content = json.choices?.[0]?.delta?.content || 
                         json.output?.text || 
                         json.choices?.[0]?.message?.content || '';
          if (content) {
            aiResponse += content;
            // 更新最后一条消息
            messages.value[messages.value.length - 1].content = aiResponse;
            await nextTick();
            scrollToBottom();
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      }
    }
  }
  
  // 如果没有收到任何内容
  if (!aiResponse) {
    messages.value[messages.value.length - 1].content = '抱歉，我无法生成回复。请检查API设置或稍后再试。';
  }
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(scrollToBottom);
}, { deep: true });

// 组件挂载时滚动到底部
onMounted(() => {
  scrollToBottom();
});
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 46px;
  padding-bottom: calc(58px + var(--safe-area-inset-bottom));
  background: var(--page-gradient);
  box-sizing: border-box;
}

:deep(.van-nav-bar) {
  background: var(--nav-color);
  backdrop-filter: blur(18px);
  box-shadow: 0 8px 24px var(--shadow-color);
}

:deep(.van-nav-bar__title) {
  color: var(--text-color);
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-hero {
  position: relative;
  margin: 12px 16px 8px;
  padding: 16px 18px;
  background: linear-gradient(135deg, var(--card-color), var(--secondary-color));
  border: 1px solid color-mix(in srgb, var(--border-color) 78%, transparent);
  border-radius: 22px;
  box-shadow: 0 12px 30px var(--shadow-color);
  overflow: hidden;
}

.chat-hero::after {
  content: '';
  position: absolute;
  right: -32px;
  top: -36px;
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: var(--primary-color-soft);
}

.chat-hero span,
.chat-hero strong,
.chat-hero p {
  position: relative;
  z-index: 1;
  display: block;
}

.chat-hero span {
  margin-bottom: 5px;
  color: var(--primary-color);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

.chat-hero strong {
  color: var(--text-color);
  font-size: 21px;
  line-height: 1.18;
  letter-spacing: -0.03em;
}

.chat-hero p {
  margin: 7px 0 0;
  color: var(--text-color-light);
  font-size: 13px;
  line-height: 1.45;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px 14px 12px;
}

.message {
  position: relative;
  margin-bottom: 12px;
  max-width: 84%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 12px 14px;
  border-radius: 18px;
  word-break: break-word;
  line-height: 1.58;
  font-size: 14px;
}

.user-message .message-content {
  color: #fff;
  background: linear-gradient(135deg, var(--primary-color), color-mix(in srgb, var(--primary-color) 74%, #ffffff));
  border-bottom-right-radius: 6px;
  box-shadow: 0 10px 24px color-mix(in srgb, var(--primary-color) 24%, transparent);
}

.ai-message .message-content {
  color: var(--text-color);
  background: var(--card-color);
  border: 1px solid color-mix(in srgb, var(--border-color) 82%, transparent);
  border-bottom-left-radius: 6px;
  box-shadow: 0 8px 22px var(--shadow-color);
}

.input-container {
  position: relative;
  padding: 12px 90px 12px 14px;
  background: var(--nav-color);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -10px 28px var(--shadow-color);
  backdrop-filter: blur(18px);
}

.chat-input {
  width: 100%;
  min-width: 0;
}

:deep(.chat-input.van-field) {
  padding: 10px 14px;
  background: var(--card-color);
  border: 1px solid var(--border-color);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

:deep(.chat-input .van-field__control) {
  color: var(--text-color);
}

:deep(.chat-input .van-field__control::placeholder) {
  color: var(--text-color-lighter);
}

.send-button {
  flex: 0 0 66px;
  align-self: flex-end;
  width: 66px;
  min-width: 66px;
  height: 40px;
  border: 0;
  border-radius: 999px;
  font-weight: 800;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--primary-color) 22%, transparent);
}

.send-button:disabled {
  opacity: 0.48;
  box-shadow: none;
}

.message-content img {
  max-width: 100%;
  border-radius: 12px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 4px 2px;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin: 0 3px;
  background-color: var(--primary-color);
  border-radius: 50%;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.55;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

:deep(pre) {
  max-width: 100%;
  padding: 12px;
  background-color: var(--secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow-x: auto;
}

:deep(code) {
  padding: 2px 5px;
  color: var(--text-color);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background-color: var(--secondary-color);
  border-radius: 6px;
}

:deep(p) {
  margin: 6px 0;
}

:deep(ul),
:deep(ol) {
  padding-left: 20px;
}

:deep(blockquote) {
  margin: 8px 0;
  padding-left: 10px;
  color: var(--text-color-light);
  border-left: 3px solid var(--primary-color);
}

:deep(a) {
  color: var(--primary-color);
  font-weight: 700;
  text-decoration: none;
}
</style>