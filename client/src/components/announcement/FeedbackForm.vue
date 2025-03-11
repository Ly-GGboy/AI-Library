<template>
  <div class="tab-content-container">
    <h3 class="panel-title">提交反馈</h3>
    
    <p class="panel-description">
      您的反馈对我们很重要！请分享您的想法、建议或遇到的问题，帮助我们改进系统。如果有更好的资源欢迎分享
    </p>
    
    <form @submit.prevent="submitForm" class="feedback-form">
      <div class="form-group">
        <label for="name" class="form-label">您的称呼</label>
        <input 
          type="text" 
          id="name" 
          v-model="form.name" 
          class="form-input"
          placeholder="请输入您的称呼（选填）"
        />
      </div>
      
      <div class="form-group">
        <label for="email" class="form-label">电子邮箱</label>
        <input 
          type="email" 
          id="email" 
          v-model="form.email" 
          class="form-input"
          placeholder="请输入您的电子邮箱（选填）"
        />
        <small v-if="emailError" class="input-error">{{ emailError }}</small>
      </div>
      
      <div class="form-group">
        <label for="type" class="form-label">反馈类型</label>
        <select id="type" v-model="form.type" class="form-select">
          <option value="suggestion">功能建议</option>
          <option value="bug">问题报告</option>
          <option value="content">内容相关</option>
          <option value="other">其他</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="content" class="form-label">反馈内容</label>
        <textarea 
          id="content" 
          v-model="form.content" 
          class="form-textarea"
          placeholder="请详细描述您的想法或遇到的问题..."
          rows="5"
          required
        ></textarea>
        <small v-if="contentError" class="input-error">{{ contentError }}</small>
      </div>
      
      <div v-if="props.error" class="form-error">
        <ExclamationCircleIcon class="error-icon" />
        <span>{{ props.error }}</span>
      </div>
      
      <div v-if="props.success" class="form-success">
        <CheckCircleIcon class="success-icon" />
        <span>{{ props.success }}</span>
      </div>
      
      <div class="form-actions">
        <button 
          type="submit" 
          class="submit-button" 
          :disabled="submitting || !isValid"
        >
          <div v-if="props.submitting" class="flex items-center">
            <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent rounded-full mr-2"></span>
            提交中...
          </div>
          <span v-else>提交反馈</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, computed } from 'vue';
import { CheckCircleIcon, ExclamationCircleIcon, InformationCircleIcon } from '@heroicons/vue/24/outline';

interface FeedbackForm {
  name: string;
  email: string;
  type: string;
  content: string;
}

const props = defineProps({
  submitting: Boolean,
  error: String,
  success: String
});

const emit = defineEmits(['submit']);

const form = ref<FeedbackForm>({
  name: '',
  email: '',
  type: 'suggestion',
  content: ''
});

const emailError = ref('');
const contentError = ref('');

// 验证邮箱格式
const validateEmail = (): boolean => {
  if (!form.value.email) return true; // 邮箱是选填的
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(form.value.email)) {
    emailError.value = '请输入有效的电子邮箱地址';
    return false;
  }
  
  emailError.value = '';
  return true;
};

// 验证内容
const validateContent = (): boolean => {
  if (!form.value.content.trim()) {
    contentError.value = '请输入反馈内容';
    return false;
  }
  
  if (form.value.content.trim().length < 5) {
    contentError.value = '反馈内容太短，请详细描述';
    return false;
  }
  
  contentError.value = '';
  return true;
};

// 计算表单是否有效
const isValid = computed(() => {
  return form.value.content.trim().length >= 5 && !emailError.value;
});

const submitForm = () => {
  // 验证表单
  const isEmailValid = validateEmail();
  const isContentValid = validateContent();
  
  if (!isEmailValid || !isContentValid) {
    return;
  }
  
  // 组装反馈数据
  const feedback = {
    ...form.value,
    timestamp: new Date().toISOString(),
    contact: form.value.email // 使用邮箱作为联系方式
  };
  
  emit('submit', feedback);
  
  // 如果提交成功，清空表单
  if (!props.error) {
    setTimeout(() => {
      form.value = {
        name: '',
        email: '',
        type: 'suggestion',
        content: ''
      };
    }, 1000);
  }
};
</script>

<style scoped>
.panel-title {
  @apply text-lg font-bold mb-3 text-gray-900 dark:text-gray-100;
}

.panel-description {
  @apply text-sm text-gray-600 dark:text-gray-400 mb-5;
}

.feedback-form {
  @apply space-y-4;
}

.form-group {
  @apply flex flex-col;
}

.form-label {
  @apply text-sm font-medium text-gray-700 dark:text-gray-300 mb-1;
}

.form-input,
.form-select,
.form-textarea {
  @apply px-3 py-2 rounded-md bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600;
  @apply text-gray-900 dark:text-gray-100;
  @apply focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-400 dark:focus:border-primary-400;
  @apply placeholder:text-gray-400 dark:placeholder:text-gray-500;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-textarea {
  @apply resize-none;
}

.input-error {
  @apply text-red-500 text-xs mt-1;
}

.form-error {
  @apply text-red-500 text-sm bg-red-50 dark:bg-red-900/20 dark:text-red-300 p-3 rounded flex items-start;
}

.error-icon {
  @apply w-4 h-4 mr-2 mt-0.5 flex-shrink-0;
}

.form-success {
  @apply text-green-600 text-sm bg-green-50 dark:bg-green-900/20 dark:text-green-300 p-3 rounded flex items-start;
}

.success-icon {
  @apply w-4 h-4 mr-2 mt-0.5 flex-shrink-0;
}

.form-note {
  @apply text-blue-600 text-sm bg-blue-50 dark:bg-blue-900/20 dark:text-blue-300 p-3 rounded flex items-start;
}

.info-icon {
  @apply w-4 h-4 mr-2 mt-0.5 flex-shrink-0;
}

.form-actions {
  @apply flex justify-end pt-2;
}

.submit-button {
  @apply px-4 py-2 rounded-md bg-primary-600 text-white font-medium hover:bg-primary-700;
  @apply dark:bg-primary-500 dark:hover:bg-primary-600;
  @apply transition-colors duration-200;
  @apply disabled:opacity-70 disabled:cursor-not-allowed;
}
</style> 