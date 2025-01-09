<template>
  <div class="pdf-viewer" ref="pdfViewerRef">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
    <div v-if="error" class="error-overlay">
      {{ error }}
    </div>
    <div class="pdf-container" :class="{ 'loading': loading }">
      <canvas ref="pdfCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'

// 设置 PDF.js worker 使用本地文件
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf/pdf.worker.min.mjs'

const props = defineProps<{
  path: string
}>()

const pdfViewerRef = ref<HTMLElement | null>(null)
const pdfCanvas = ref<HTMLCanvasElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const currentPage = ref(1)
const scale = ref(1.5)

// 重要：将 pdfDoc 设置为非响应式变量
let pdfDoc: any = null

// 清理函数
const cleanup = () => {
  if (pdfDoc) {
    try {
      pdfDoc.destroy()
    } catch (e) {
      console.error('Error during cleanup:', e)
    }
    pdfDoc = null
  }
}

// 渲染页面
async function renderPage() {
  const canvas = pdfCanvas.value
  if (!canvas) {
    error.value = 'Canvas 元素未找到'
    console.error('Canvas element not found')
    return
  }

  if (!pdfDoc) {
    error.value = 'PDF 文档未加载'
    console.error('PDF document not loaded')
    return
  }

  try {
    console.log('Rendering page:', currentPage.value)
    const page = await pdfDoc.getPage(currentPage.value)
    const context = canvas.getContext('2d')
    
    if (!context) {
      throw new Error('无法获取 canvas 上下文')
    }

    const viewport = page.getViewport({ scale: scale.value })
    
    // 设置 canvas 尺寸
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    // 清除之前的内容
    context.clearRect(0, 0, canvas.width, canvas.height)

    // 渲染页面
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }

    await page.render(renderContext).promise
    console.log('Page rendered successfully:', currentPage.value)
  } catch (err) {
    console.error('Error rendering page:', err)
    error.value = err instanceof Error ? err.message : '渲染 PDF 页面失败'
  }
}

// 初始化 PDF
async function initPDF() {
  try {
    cleanup()
    loading.value = true
    error.value = null
    
    console.log('Loading PDF:', props.path)
    const loadingTask = pdfjsLib.getDocument(`/api/docs/content/${props.path}`)
    
    // 重要：直接赋值给非响应式变量
    pdfDoc = await loadingTask.promise
    console.log('PDF loaded:', pdfDoc.numPages, 'pages')
    
    await renderPage()
  } catch (err) {
    console.error('Error loading PDF:', err)
    error.value = err instanceof Error ? err.message : '加载 PDF 失败'
  } finally {
    loading.value = false
  }
}

// 监听路径变化
watch(() => props.path, () => {
  console.log('PDF path changed:', props.path)
  initPDF()
})

// 组件挂载时初始化
onMounted(() => {
  console.log('PDFViewer mounted, canvas ref:', pdfCanvas.value)
  initPDF()
})

// 组件卸载时清理
onBeforeUnmount(() => {
  cleanup()
})
</script>

<style scoped>
.pdf-viewer {
  width: 100%;
  height: 100%;
  position: relative;
  background: #f5f5f5;
  overflow: hidden;
}

.pdf-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
  padding: 20px;
}

.pdf-container.loading {
  visibility: hidden;
}

canvas {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  max-width: 100%;
  height: auto;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-text {
  color: #666;
  font-size: 16px;
}

.error-overlay {
  background: #fee2e2;
  color: #dc2626;
  padding: 20px;
  text-align: center;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 暗色主题支持 */
:root.dark .pdf-viewer {
  background: #1a1a1a;
}

:root.dark canvas {
  background: #2d2d2d;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

:root.dark .loading-overlay {
  background: rgba(26, 26, 26, 0.9);
}

:root.dark .loading-text {
  color: #999;
}

:root.dark .error-overlay {
  background: #422c2c;
  color: #ef4444;
}
</style>
