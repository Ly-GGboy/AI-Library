<template>
  <div class="pdf-viewer" ref="pdfViewerRef">
    <div class="pdf-container" ref="pdfContainer">
      <div class="pdf-content" :class="{ 'sidebar-visible': sidebarExpanded }">
        <div v-if="loading" class="loading-overlay">
          <div class="loading-spinner">
            <div class="book">
              <div class="book-page"></div>
              <div class="book-page"></div>
              <div class="book-page"></div>
              <div class="book-cover"></div>
            </div>
          </div>
          <div class="loading-text">正在加载文档...</div>
        </div>
        <div v-if="error" class="error-overlay">
          {{ error }}
        </div>
        <div class="pages-container">
          <div v-for="pageNum in renderedPages" :key="pageNum" class="page-container">
            <canvas :ref="el => setCanvasRef(el as HTMLCanvasElement, pageNum)" :id="`page-${pageNum}`"></canvas>
          </div>
          <div v-if="hasMorePages" class="load-more-trigger" ref="loadMoreTrigger"></div>
        </div>
      </div>
      <div class="pdf-sidebar" 
           :class="{ 'collapsed': !sidebarExpanded }"
           @wheel.stop
           @touchmove.stop
           @mouseenter="expandSidebar"
           @mouseleave="collapseSidebar">
        <div class="sidebar-toggle">
          <svg v-if="sidebarExpanded" class="toggle-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
          </svg>
          <svg v-else class="toggle-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="toggle-text" v-show="sidebarExpanded">{{ hasOutline ? '目录' : '页面' }}</span>
        </div>
        <div class="sidebar-content" 
             v-show="sidebarExpanded"
             @wheel.stop
             @touchmove.stop>
          <template v-if="hasOutline">
            <div v-for="(item, index) in flattenedOutline" :key="index" 
                 class="outline-item"
                 :class="{ 'active': isActiveOutlineItem(item) }"
                 :style="{ paddingLeft: item.level * 12 + 'px' }"
                 @click="navigateToDestination(item)">
              <span class="outline-title">{{ item.title }}</span>
              <span class="outline-page" v-if="item.pageNumber">{{ item.pageNumber }}</span>
            </div>
          </template>
          <template v-else>
            <div v-for="pageNum in totalPages" :key="pageNum" 
                 class="page-item"
                 :class="{ 'active': currentPage === pageNum }"
                 @click="scrollToPage(pageNum)">
              第 {{ pageNum }} 页
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import { GlobalWorkerOptions } from 'pdfjs-dist'

// 设置 worker 路径
GlobalWorkerOptions.workerSrc = '/pdf/pdf.worker.min.mjs'

const props = defineProps<{
  path: string
}>()

const pdfViewerRef = ref<HTMLElement | null>(null)
const pdfContainer = ref<HTMLElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const scale = ref(1.5)
const totalPages = ref(0)
const pageCanvases = new Map<number, HTMLCanvasElement>()
const currentPage = ref(1)
const outline = ref<any[]>([])
const hasOutline = ref(false)
const sidebarExpanded = ref(false)

// 重要：将 pdfDoc 设置为非响应式变量
let pdfDoc: any = null

// 添加渲染锁
const renderLocks = new Map<number, boolean>();

// 添加书签位置跟踪
const currentDestination = ref<{
  pageNumber: number,
  top: number | null,
  left: number | null,
  zoom: number | null
} | null>(null);

// 添加暗色模式状态
const isDarkMode = ref(false)

// 监听系统主题变化
function updateTheme() {
  isDarkMode.value = document.documentElement.classList.contains('dark')
}

// 设置 canvas 引用
const setCanvasRef = (el: HTMLCanvasElement | null, pageNum: number) => {
  if (el) {
    pageCanvases.set(pageNum, el)
  }
}

// 添加渲染页面的状态管理
const renderedPages = ref<number[]>([]);
const hasMorePages = computed(() => {
  const lastRenderedPage = renderedPages.value[renderedPages.value.length - 1] || 0;
  return lastRenderedPage < totalPages.value;
});

// 修改初始化 PDF 函数
async function initPDF() {
  loading.value = true;
  error.value = null;
  
  try {
    // 清理之前的状态
    cleanup();
    
    // 加载 PDF 文档
    pdfDoc = await pdfjsLib.getDocument(`/api/docs/content/${props.path}`).promise;
    totalPages.value = pdfDoc.numPages;
    
    // 加载大纲
    const outlineData = await pdfDoc.getOutline();
    if (outlineData && outlineData.length > 0) {
      const processedOutline = await processOutline(outlineData);
      outline.value = processedOutline;
      hasOutline.value = true;
    } else {
      outline.value = [];
      hasOutline.value = false;
    }
    
    // 渲染页面
    await renderInitialPages();
    setupIntersectionObserver();
    
  } catch (err: any) {
    console.error('Error loading PDF:', err);
    error.value = `加载PDF失败: ${err.message}`;
  } finally {
    loading.value = false;
  }
}

// 修改清理函数
function cleanup() {
  if (pdfDoc) {
    try {
      pdfDoc.destroy();
    } catch (e) {
      console.error('Error during cleanup:', e);
    }
    pdfDoc = null;
  }
  
  // 清理画布
  pageCanvases.forEach((canvas) => {
    const context = canvas.getContext('2d');
    if (context) {
      context.clearRect(0, 0, canvas.width, canvas.height);
    }
  });
  pageCanvases.clear();
  renderLocks.clear();
  
  // 重置所有状态
  totalPages.value = 0;
  currentPage.value = 1;
  renderedPages.value = [];
  error.value = null;
  outline.value = [];
  hasOutline.value = false;
  currentDestination.value = null;
  sidebarExpanded.value = false;
}

// 渲染初始页面
async function renderInitialPages() {
  const initialPageCount = 3; // 初始加载3页
  const pagesToRender = [];
  
  for (let i = 1; i <= Math.min(initialPageCount, totalPages.value); i++) {
    pagesToRender.push(i);
  }
  
  renderedPages.value = pagesToRender;
  await renderVisiblePages();
}

// 设置 Intersection Observer
function setupIntersectionObserver() {
  const options = {
    root: pdfContainer.value,
    rootMargin: '100px',
    threshold: 0.1
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        loadMorePages();
      }
    });
  }, options);
  
  // 监视加载更多的触发器
  const loadMoreTrigger = document.querySelector('.load-more-trigger');
  if (loadMoreTrigger) {
    observer.observe(loadMoreTrigger);
  }
}

// 加载更多页面
async function loadMorePages() {
  if (!hasMorePages.value) return;
  
  const lastRenderedPage = renderedPages.value[renderedPages.value.length - 1] || 0;
  const nextPages = [];
  const pageCount = 3; // 每次加载3页
  
  for (let i = lastRenderedPage + 1; i <= Math.min(lastRenderedPage + pageCount, totalPages.value); i++) {
    nextPages.push(i);
  }
  
  renderedPages.value = [...renderedPages.value, ...nextPages];
  await renderVisiblePages();
}

// 修改渲染可见页面的函数
async function renderVisiblePages() {
  if (!pdfContainer.value) return;

  const pages = Array.from(pageCanvases.entries());
  const visiblePages = new Set<number>();
  
  // 找出当前可见的页面
  for (const [pageNum, canvas] of pages) {
    if (isElementInViewport(canvas)) {
      visiblePages.add(pageNum);
    }
  }

  // 添加缓冲区页面
  const buffer = 1;
  const pagesToRender = new Set<number>();
  
  visiblePages.forEach(pageNum => {
    for (let i = Math.max(1, pageNum - buffer); i <= Math.min(totalPages.value, pageNum + buffer); i++) {
      if (renderedPages.value.includes(i)) {
        pagesToRender.add(i);
      }
    }
  });

  // 串行渲染页面
  for (const pageNum of pagesToRender) {
    if (!renderLocks.get(pageNum)) {
      await renderPage(pageNum);
    }
  }
}

// 获取PDF大纲
async function getOutline() {
  if (!pdfDoc) return
  
  try {
    const outlineData = await pdfDoc.getOutline()
    if (outlineData && outlineData.length > 0) {
      hasOutline.value = true
      outline.value = await processOutline(outlineData)
    } else {
      hasOutline.value = false
      outline.value = []
    }
  } catch (err) {
    console.error('Error getting outline:', err)
    hasOutline.value = false
    outline.value = []
  }
}

// 修改处理大纲数据的函数
async function processOutline(items: any[], level = 0): Promise<any[]> {
  const processedItems = [];
  
  for (const item of items) {
    let pageNumber = null;
    let destArray = null;
    
    if (item.dest) {
      try {
        // 获取目标信息
        destArray = typeof item.dest === 'string' 
          ? await pdfDoc.getDestination(item.dest)
          : item.dest;
          
        if (destArray && destArray.length > 0 && destArray[0]) {
          // 获取页面引用和页码
          const pageRef = destArray[0];
          const pageIndex = await pdfDoc.getPageIndex(pageRef);
          pageNumber = pageIndex + 1;
          
          console.log(`Processed bookmark: ${item.title}`, {
            pageNumber,
            destArray
          });
        }
      } catch (err) {
        console.error('Error processing outline item:', err);
      }
    }

    const processedItem = {
      title: item.title,
      dest: destArray,      // 保存原始目标数组
      level,
      pageNumber,
      children: item.items ? await processOutline(item.items, level + 1) : []
    };
    processedItems.push(processedItem);
  }
  
  return processedItems;
}

// 修改模板部分的大纲显示逻辑
function flattenOutline(items: any[]): any[] {
  return items.reduce((acc, item) => {
    acc.push(item)
    if (item.children && item.children.length > 0) {
      acc.push(...flattenOutline(item.children))
    }
    return acc
  }, [])
}

// 在 script setup 顶部添加计算属性
const flattenedOutline = computed(() => {
  return hasOutline.value ? flattenOutline(outline.value) : []
})

// 修改激活状态判断函数
function isActiveOutlineItem(item: any): boolean {
  if (!item.pageNumber) return false;
  
  // 如果页码不匹配，直接返回 false
  if (currentPage.value !== item.pageNumber) return false;
  
  // 如果没有当前目标位置信息，只判断页码
  if (!currentDestination.value) return true;
  
  // 如果是当前目标项，检查具体位置
  if (currentDestination.value.pageNumber === item.pageNumber && item.dest) {
    const [, , , top] = item.dest;
    const currentTop = currentDestination.value.top;
    
    // 如果都有具体位置，进行比较
    if (typeof top === 'number' && typeof currentTop === 'number') {
      return Math.abs(top - currentTop) < 1;
    }
  }
  
  // 如果在同一页但没有具体位置信息，返回 true
  return true;
}

// 获取下一个同级或更高级别的大纲项
function getNextOutlineItem(currentItem: any): any {
  const items = flattenedOutline.value;
  const currentIndex = items.findIndex(item => item === currentItem);
  if (currentIndex === -1 || currentIndex === items.length - 1) return null;

  // 查找下一个同级或更高级别的项
  for (let i = currentIndex + 1; i < items.length; i++) {
    if (items[i].level <= currentItem.level) {
      return items[i];
    }
  }
  return null;
}

// 修改导航函数
async function navigateToDestination(item: any) {
  try {
    if (!item.dest || !item.pageNumber) {
      console.error('Invalid bookmark:', item);
      return;
    }
    
    console.log('Navigating to bookmark:', item);
    
    // 标记目标页面为加载状态
    const targetPageContainer = document.querySelector(`#page-${item.pageNumber}`)?.parentElement;
    if (targetPageContainer) {
      targetPageContainer.classList.add('loading');
    }
    
    // 确保目标页面及其前后页面已加载到渲染列表中
    const buffer = 10;
    const targetPage = item.pageNumber;
    const startPage = Math.max(1, targetPage - buffer);
    const endPage = Math.min(totalPages.value, targetPage + buffer);
    
    // 计算需要加载的页面
    const pagesToAdd = [];
    for (let i = startPage; i <= endPage; i++) {
      if (!renderedPages.value.includes(i)) {
        pagesToAdd.push(i);
      }
    }
    
    if (pagesToAdd.length > 0) {
      // 按照与目标页面的距离排序，优先加载离目标页面近的页面
      pagesToAdd.sort((a, b) => {
        const distA = Math.abs(a - targetPage);
        const distB = Math.abs(b - targetPage);
        return distA - distB;
      });
      
      // 更新渲染列表
      renderedPages.value = [...new Set([...renderedPages.value, ...pagesToAdd])].sort((a, b) => a - b);
      
      // 等待一下以确保 DOM 更新
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // 优先渲染目标页面
      await renderPage(targetPage);
      
      // 异步渲染其他页面
      Promise.all(pagesToAdd
        .filter(pageNum => pageNum !== targetPage)
        .map(pageNum => renderPage(pageNum))
      ).catch(err => {
        console.error('Error rendering buffer pages:', err);
      });
    }
    
    // 获取目标页面
    const page = await pdfDoc.getPage(targetPage);
    
    // 获取目标位置信息
    let destArray = item.dest;
    if (typeof destArray === 'string') {
      destArray = await pdfDoc.getDestination(destArray);
    }
    
    // 处理目标数组
    if (!Array.isArray(destArray)) {
      throw new Error('Invalid destination array');
    }
    
    // 获取页面元素
    const pageElement = document.getElementById(`page-${targetPage}`);
    if (!pageElement || !pdfContainer.value) {
      throw new Error('Page element or container not found');
    }
    
    // 计算目标位置
    const viewport = page.getViewport({ scale: scale.value });
    let targetY = 0;
    
    // 解析目标数组，处理引用对象
    let destType: string | undefined;
    let left: number | null = null;
    let top: number | null = null;
    let zoom: number | null = null;
    
    // 遍历数组找到实际的参数
    for (let i = 0; i < destArray.length; i++) {
      const item = destArray[i];
      if (item && typeof item === 'object' && item.name === 'XYZ') {
        destType = 'XYZ';
        left = destArray[i + 1] || null;
        top = destArray[i + 2] || null;
        zoom = destArray[i + 3] || null;
        break;
      }
    }
    
    if (destType === 'XYZ' && typeof top === 'number') {
      const canvas = pageElement.querySelector('canvas');
      if (canvas) {
        targetY = viewport.height - (top * viewport.scale);
        targetY = Math.max(0, Math.min(targetY, canvas.height));
      }
    }
    
    // 计算滚动位置
    const containerRect = pdfContainer.value.getBoundingClientRect();
    const scrollTop = pageElement.offsetTop + targetY;
    
    // 调整目标位置，使其位于视口的黄金分割点（约0.382）
    const adjustment = containerRect.height * 0.382;
    const finalScrollTop = Math.max(0, scrollTop - adjustment);
    
    // 创建一个平滑的滚动动画
    if (!pdfContainer.value) {
      console.error('PDF container not found');
      return;
    }
    
    const container = pdfContainer.value; // 保存引用以确保动画过程中的稳定性
    const startPosition = container.scrollTop;
    const distance = finalScrollTop - startPosition;
    const duration = 800;
    const startTime = performance.now();
    
    function easeInOutCubic(t: number): number {
      return t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    
    function scrollAnimation(currentTime: number) {
      // 确保容器仍然存在
      if (!container) {
        console.warn('Container lost during animation');
        if (targetPageContainer) {
          targetPageContainer.classList.remove('loading');
        }
        return;
      }
      
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easedProgress = easeInOutCubic(progress);
      const currentPosition = startPosition + distance * easedProgress;
      
      try {
        container.scrollTop = currentPosition;
        
        if (progress < 1) {
          requestAnimationFrame(scrollAnimation);
        } else {
          // 动画完成后移除加载状态
          if (targetPageContainer) {
            targetPageContainer.classList.remove('loading');
          }
          // 更新状态
          currentPage.value = targetPage;
          currentDestination.value = {
            pageNumber: targetPage,
            top: top as number | null,
            left: left as number | null,
            zoom: zoom as number | null
          };
        }
      } catch (err) {
        console.error('Error during scroll animation:', err);
        if (targetPageContainer) {
          targetPageContainer.classList.remove('loading');
        }
      }
    }
    
    requestAnimationFrame(scrollAnimation);
    
  } catch (err) {
    console.error('Navigation failed:', err);
    // 如果精确定位失败，至少跳转到对应页面
    try {
      await scrollToPage(item.pageNumber);
    } catch (scrollErr) {
      console.error('Fallback scroll failed:', scrollErr);
    }
  }
}

// 修改滚动到指定页面的函数
async function scrollToPage(pageNum: number) {
  console.log('Scrolling to page:', pageNum);
  if (!pdfContainer.value) return;
  
  try {
    const targetPageContainer = document.querySelector(`#page-${pageNum}`)?.parentElement;
    if (targetPageContainer) {
      targetPageContainer.classList.add('loading');
    }
    
    // 确保目标页面及其前后页面已加载
    const buffer = 10;
    const startPage = Math.max(1, pageNum - buffer);
    const endPage = Math.min(totalPages.value, pageNum + buffer);
    
    const pagesToAdd = [];
    for (let i = startPage; i <= endPage; i++) {
      if (!renderedPages.value.includes(i)) {
        pagesToAdd.push(i);
      }
    }
    
    if (pagesToAdd.length > 0) {
      // 按照与目标页面的距离排序
      pagesToAdd.sort((a, b) => {
        const distA = Math.abs(a - pageNum);
        const distB = Math.abs(b - pageNum);
        return distA - distB;
      });
      
      renderedPages.value = [...new Set([...renderedPages.value, ...pagesToAdd])].sort((a, b) => a - b);
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // 优先渲染目标页面
      await renderPage(pageNum);
      
      // 异步渲染其他页面
      Promise.all(pagesToAdd
        .filter(p => p !== pageNum)
        .map(p => renderPage(p))
      ).catch(err => {
        console.error('Error rendering buffer pages:', err);
      });
    }
    
    const pageElement = document.getElementById(`page-${pageNum}`);
    if (!pageElement || !pdfContainer.value) return;
    
    const containerRect = pdfContainer.value.getBoundingClientRect();
    const scrollTop = Math.max(0, pageElement.offsetTop - (containerRect.height * 0.382));
    
    const container = pdfContainer.value; // 保存引用以确保动画过程中的稳定性
    const startPosition = container.scrollTop;
    const distance = scrollTop - startPosition;
    const duration = 800;
    const startTime = performance.now();
    
    function easeInOutCubic(t: number): number {
      return t < 0.5
        ? 4 * t * t * t
        : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    
    function scrollAnimation(currentTime: number) {
      // 确保容器仍然存在
      if (!container) {
        console.warn('Container lost during animation');
        if (targetPageContainer) {
          targetPageContainer.classList.remove('loading');
        }
        return;
      }
      
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easedProgress = easeInOutCubic(progress);
      const currentPosition = startPosition + distance * easedProgress;
      
      try {
        container.scrollTop = currentPosition;
        
        if (progress < 1) {
          requestAnimationFrame(scrollAnimation);
        } else {
          // 动画完成后移除加载状态
          if (targetPageContainer) {
            targetPageContainer.classList.remove('loading');
          }
          // 更新当前页码
          currentPage.value = pageNum;
        }
      } catch (err) {
        console.error('Error during scroll animation:', err);
        if (targetPageContainer) {
          targetPageContainer.classList.remove('loading');
        }
      }
    }
    
    requestAnimationFrame(scrollAnimation);
    
  } catch (err: any) {
    console.error('Error scrolling to page:', err);
    error.value = `跳转失败: ${err.message}`;
  }
}

// 更新当前页码
function updateCurrentPage() {
  if (!pdfContainer.value) return;
  
  const containerRect = pdfContainer.value.getBoundingClientRect();
  const pages = Array.from(pageCanvases.keys());
  
  for (const pageNum of pages) {
    const pageElement = document.getElementById(`page-${pageNum}`);
    if (pageElement && isElementInViewport(pageElement)) {
      currentPage.value = pageNum;
      // 如果不是通过书签跳转，清除当前目标位置
      if (!currentDestination.value || currentDestination.value.pageNumber !== pageNum) {
        currentDestination.value = null;
      }
      break;
    }
  }
}

// 判断元素是否在视口中
function isElementInViewport(el: HTMLElement) {
  const rect = el.getBoundingClientRect()
  return (
    rect.top >= -rect.height &&
    rect.top <= (window.innerHeight || document.documentElement.clientHeight)
  )
}

// 处理滚动事件
let scrollTimeout: any = null
function handleScroll() {
  if (scrollTimeout) {
    clearTimeout(scrollTimeout);
  }
  
  scrollTimeout = setTimeout(async () => {
    await renderVisiblePages();
    updateCurrentPage();
    
    // 清除当前目标位置，因为用户已经手动滚动
    if (currentDestination.value) {
      currentDestination.value = null;
    }
  }, 100);
}

// 修改监听函数
watch(() => props.path, async (newPath, oldPath) => {
  if (newPath === oldPath) return;
  
  loading.value = true;  // 确保设置加载状态
  try {
    await initPDF();
  } catch (err) {
    console.error('Error switching PDF:', err);
  }
}, { immediate: true });  // 添加 immediate: true 确保首次加载时也触发

// 展开侧边栏
function expandSidebar() {
  sidebarExpanded.value = true
}

// 收起侧边栏
function collapseSidebar() {
  sidebarExpanded.value = false
}

// 组件挂载时初始化
onMounted(() => {
  console.log('PDFViewer mounted')
  initPDF()
  window.addEventListener('scroll', handleScroll, { passive: true })
  
  // 初始化主题
  updateTheme()
  
  // 监听主题变化
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        updateTheme()
      }
    })
  })
  
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class']
  })
})

// 组件卸载时清理
onBeforeUnmount(() => {
  cleanup()
  window.removeEventListener('scroll', handleScroll)
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
  }
})

// 渲染单页
async function renderPage(pageNum: number) {
  const canvas = pageCanvases.get(pageNum);
  if (!canvas) {
    console.error(`Canvas for page ${pageNum} not found`);
    return;
  }

  // 检查是否正在渲染
  if (renderLocks.get(pageNum)) {
    return;
  }

  // 如果页面已经渲染过且内容不为空，则跳过
  const context = canvas.getContext('2d');
  if (context) {
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    if (imageData.data.some(pixel => pixel !== 0)) {
      return;
    }
  }

  // 设置渲染锁
  renderLocks.set(pageNum, true);
  
  try {
    const page = await pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: scale.value });
    
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    const renderContext = {
      canvasContext: canvas.getContext('2d'),
      viewport: viewport
    };
    
    await page.render(renderContext).promise;
  } catch (err) {
    console.error(`Error rendering page ${pageNum}:`, err);
  } finally {
    renderLocks.set(pageNum, false);
  }
}

// 添加计算属性获取文件名
const fileName = computed(() => {
  const parts = props.path.split('/');
  const lastPart = parts[parts.length - 1];
  return lastPart.replace(/\.pdf$/i, '');
});
</script>

<style scoped>
:root {
  --dark-bg-primary: rgb(17, 24, 39);
  --dark-bg-secondary: rgb(31, 41, 55);
  --dark-text-primary: rgb(209, 213, 219);
  --dark-text-secondary: rgb(156, 163, 175);
  --dark-accent: rgb(59, 130, 246);
  --dark-hover: rgba(55, 65, 81, 0.7);
  --dark-active-bg: rgb(30, 41, 59);
  --dark-active-text: rgb(96, 165, 250);
  --dark-active-border: rgb(96, 165, 250);
  --dark-border: rgba(75, 85, 99, 1);
  --dark-shadow: rgba(0, 0, 0, 0.4);
  
  --light-bg-primary: rgb(255, 255, 255);
  --light-bg-secondary: rgb(249, 250, 251);
  --light-text-primary: rgb(17, 24, 39);
  --light-text-secondary: rgb(107, 114, 128);
  --light-accent: rgb(37, 99, 235);
  --light-hover: rgba(243, 244, 246, 0.9);
  --light-active-bg: rgb(243, 244, 246);
  --light-active-text: rgb(37, 99, 235);
  --light-active-border: rgb(37, 99, 235);
  --light-border: rgb(229, 231, 235);
  --light-shadow: rgba(0, 0, 0, 0.1);
}

.pdf-viewer {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: v-bind('isDarkMode ? "rgb(17, 24, 39)" : "rgb(255, 255, 255)"');
  color: v-bind('isDarkMode ? "rgb(209, 213, 219)" : "rgb(17, 24, 39)"');
}

.pdf-container {
  flex: 1;
  width: 100%;
  height: 100vh;  /* 修改为全屏高度 */
  overflow: auto;
  position: relative;
  background: v-bind('isDarkMode ? "rgb(17, 24, 39)" : "rgb(255, 255, 255)"');
  scrollbar-width: thin;
  scrollbar-color: v-bind('isDarkMode ? "rgba(75, 85, 99, 0.3) rgba(31, 41, 55, 0.2)" : "rgba(209, 213, 219, 0.5) rgba(249, 250, 251, 0.2)"');
}

.pdf-container::-webkit-scrollbar {
  width: 6px;
}

.pdf-container::-webkit-scrollbar-track {
  background: v-bind('isDarkMode ? "rgba(31, 41, 55, 0.2)" : "rgba(249, 250, 251, 0.2)"');
}

.pdf-container::-webkit-scrollbar-thumb {
  background: v-bind('isDarkMode ? "rgba(75, 85, 99, 0.3)" : "rgba(209, 213, 219, 0.5)"');
  border-radius: 3px;
}

.pdf-content {
  position: relative;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  transition: all 0.3s ease;
  z-index: 1;
  min-height: clamp(300px, 50vh, 600px);
}

.page-container {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  margin: 1rem 0;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.page-container.loading {
  opacity: 0.6;
}

.pdf-page {
  width: 100%;
  height: auto;
}

.pdf-sidebar {
  position: fixed;
  top: 5rem;
  right: 2rem;
  width: 320px;
  max-height: min(800px, calc(100vh - 7rem));
  background-color: v-bind('isDarkMode ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)"');
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid v-bind('isDarkMode ? "rgba(75, 85, 99, 0.3)" : "rgba(229, 231, 235, 0.5)"');
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: v-bind('isDarkMode ? "0 8px 32px rgba(0, 0, 0, 0.4)" : "0 8px 32px rgba(0, 0, 0, 0.1)"');
  z-index: 100;
}

.pdf-sidebar.collapsed {
  width: 44px;
  height: 44px;
  background-color: v-bind('isDarkMode ? "rgba(31, 41, 55, 0.8)" : "rgba(255, 255, 255, 0.8)"');
  border-radius: 22px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.pdf-sidebar.collapsed .sidebar-toggle {
  padding: 0;
  width: 44px;
  height: 44px;
  margin: 0;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 22px;
}

.pdf-sidebar.collapsed .toggle-icon {
  margin: 0;
}

.pdf-sidebar.collapsed .toggle-text {
  display: none;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.75rem 0.5rem;
  margin: 0 0.25rem;
  scrollbar-width: thin;
  scrollbar-color: v-bind('isDarkMode ? "rgba(75, 85, 99, 0.3) rgba(31, 41, 55, 0.2)" : "rgba(209, 213, 219, 0.5) rgba(249, 250, 251, 0.2)"');
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}

.sidebar-content::-webkit-scrollbar {
  width: 4px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: transparent;
  margin: 4px 0;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: v-bind('isDarkMode ? "rgba(75, 85, 99, 0.3)" : "rgba(209, 213, 219, 0.5)"');
  border-radius: 2px;
}

.sidebar-content::-webkit-scrollbar-thumb:hover {
  background: v-bind('isDarkMode ? "rgba(75, 85, 99, 0.5)" : "rgba(209, 213, 219, 0.7)"');
}

.sidebar-item {
  padding: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-radius: 4px;
}

.sidebar-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.sidebar-toggle {
  position: sticky;
  top: 0;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: transparent;
  font-weight: 500;
  font-size: 0.9rem;
  color: v-bind('isDarkMode ? "var(--dark-text-primary)" : "var(--light-text-primary)"');
  z-index: 2;
  flex-shrink: 0;
  border-bottom: 1px solid v-bind('isDarkMode ? "rgba(75, 85, 99, 0.2)" : "rgba(229, 231, 235, 0.5)"');
  margin: 0 0.5rem;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-toggle:hover {
  background-color: v-bind('isDarkMode ? "rgba(55, 65, 81, 0.5)" : "rgba(243, 244, 246, 0.8)"');
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: v-bind('isDarkMode ? "rgba(17, 24, 39, 0.85)" : "rgba(255, 255, 255, 0.85)"');
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 100;
  animation: fadeIn 0.3s ease-out;
  padding: 2rem;
}

.loading-spinner {
  position: relative;
  width: clamp(80px, 15vw, 160px);  /* 响应式宽度 */
  height: clamp(60px, 10vw, 120px);  /* 响应式高度 */
  perspective: 800px;
  transform-style: preserve-3d;
  animation: floatBook 3s ease-in-out infinite;
  margin: 0 auto;
  margin-top: clamp(2rem, 10vh, 6rem);  /* 响应式上边距 */
}

.book {
  position: absolute;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transform: rotateX(60deg) rotateZ(-10deg);
  animation: tiltBook 6s ease-in-out infinite;
  will-change: transform;
}

.book-page {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 4px;
  background: v-bind('isDarkMode ? "rgb(96, 165, 250)" : "rgb(37, 99, 235)"');
  transform-origin: left center;
  animation: flipPage 2.4s ease-in-out infinite;
  box-shadow: v-bind('isDarkMode ? "0 0 15px rgba(147, 197, 253, 0.3)" : "0 0 15px rgba(37, 99, 235, 0.2)"');
  will-change: transform, filter;
}

.book-page:nth-child(1) {
  animation-delay: 0s;
  background: v-bind('isDarkMode ? "rgb(96, 165, 250)" : "rgb(37, 99, 235)"');
  opacity: 0.95;
}

.book-page:nth-child(2) {
  animation-delay: 0.4s;
  background: v-bind('isDarkMode ? "rgb(147, 197, 253)" : "rgb(59, 130, 246)"');
  opacity: 0.85;
}

.book-page:nth-child(3) {
  animation-delay: 0.8s;
  background: v-bind('isDarkMode ? "rgb(191, 219, 254)" : "rgb(96, 165, 250)"');
  opacity: 0.75;
}

.book-cover {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 4px;
  background: v-bind('isDarkMode ? "rgb(30, 41, 59)" : "rgb(243, 244, 246)"');
  transform: translateZ(-8px);
  box-shadow: v-bind('isDarkMode ? "0 0 30px rgba(0, 0, 0, 0.6)" : "0 0 30px rgba(0, 0, 0, 0.15)"');
}

.book-cover::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    v-bind('isDarkMode ? "rgba(255, 255, 255, 0.1)" : "rgba(255, 255, 255, 0.6)"') 0%,
    v-bind('isDarkMode ? "rgba(255, 255, 255, 0)" : "rgba(255, 255, 255, 0)"') 50%);
  border-radius: inherit;
  animation: shimmer 3s ease-in-out infinite;
}

@keyframes flipPage {
  0% {
    transform: rotateY(0deg);
    filter: brightness(1);
  }
  40% {
    transform: rotateY(-180deg);
    filter: brightness(1.2);
  }
  100% {
    transform: rotateY(-180deg);
    filter: brightness(1);
  }
}

@keyframes floatBook {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(clamp(-8px, -1.5vw, -15px));
  }
}

@keyframes tiltBook {
  0%, 100% {
    transform: rotateX(60deg) rotateZ(clamp(-8deg, -1.5vw, -12deg));
  }
  50% {
    transform: rotateX(60deg) rotateZ(clamp(3deg, 0.8vw, 6deg));
  }
}

@keyframes shimmer {
  0%, 100% {
    opacity: 0.5;
    transform: translateX(-100%) skewX(-15deg);
  }
  50% {
    opacity: 1;
    transform: translateX(100%) skewX(-15deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.error-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: v-bind('isDarkMode ? "var(--dark-bg-secondary)" : "var(--light-bg-secondary)"');
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  color: #f44336;
  text-align: center;
  z-index: 98;
}

.outline-item {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0.75rem;
  margin: 0.25rem 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: v-bind('isDarkMode ? "var(--dark-text-primary)" : "var(--light-text-primary)"');
  font-size: 0.9rem;
  line-height: 1.5;
  letter-spacing: 0.01em;
}

.outline-item:hover {
  background-color: v-bind('isDarkMode ? "rgba(55, 65, 81, 0.5)" : "rgba(243, 244, 246, 0.8)"');
  transform: translateX(2px);
}

.outline-item.active {
  background-color: v-bind('isDarkMode ? "rgb(30, 41, 59)" : "rgb(243, 244, 246)"');
  font-weight: 500;
  transform: translateX(4px);
}

.outline-item.active::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 1.5px;
  background-color: v-bind('isDarkMode ? "rgb(96, 165, 250)" : "rgb(37, 99, 235)"');
}

.outline-title {
  flex: 1;
  margin-right: 1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
  font-weight: inherit;
}

.outline-page {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.125rem 0.5rem;
  border-radius: 6px;
  background-color: v-bind('isDarkMode ? "rgba(55, 65, 81, 0.3)" : "rgba(243, 244, 246, 0.8)"');
  color: v-bind('isDarkMode ? "rgba(209, 213, 219, 0.8)" : "rgba(107, 114, 128, 0.8)"');
  min-width: 2rem;
  text-align: center;
  transition: all 0.2s ease;
}

.outline-item:hover .outline-page {
  transform: scale(1.05);
}

.outline-item.active .outline-page {
  background-color: v-bind('isDarkMode ? "rgba(96, 165, 250, 0.15)" : "rgba(37, 99, 235, 0.1)"');
  color: v-bind('isDarkMode ? "rgb(96, 165, 250)" : "rgb(37, 99, 235)"');
  transform: scale(1.05);
}

.page-item {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0.6rem 0.75rem;
  margin: 0.125rem 0.375rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  color: v-bind('isDarkMode ? "var(--dark-text-primary)" : "var(--light-text-primary)"');
  font-size: 0.9rem;
  line-height: 1.5;
  letter-spacing: 0.01em;
}

.page-item:hover {
  background-color: v-bind('isDarkMode ? "rgba(55, 65, 81, 0.5)" : "rgba(243, 244, 246, 0.8)"');
}

.page-item.active {
  background-color: v-bind('isDarkMode ? "rgb(30, 41, 59)" : "rgb(243, 244, 246)"');
  font-weight: 500;
}

.page-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 2px;
  border-radius: 1px;
  background-color: v-bind('isDarkMode ? "rgb(96, 165, 250)" : "rgb(37, 99, 235)"');
}

canvas {
  max-width: 100%;
  height: auto;
  box-shadow: v-bind('isDarkMode ? "0 2px 4px var(--dark-shadow)" : "0 2px 4px var(--light-shadow)"');
  border-radius: 4px;
  filter: v-bind('isDarkMode ? "invert(0.9) hue-rotate(180deg)" : "none"');
}

.pages-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.load-more-trigger {
  width: 100%;
  height: 20px;
  margin: 1rem 0;
}

.toggle-icon {
  transition: transform 0.3s ease;
  flex-shrink: 0;
  opacity: 0.8;
}

.sidebar-toggle:hover .toggle-icon {
  opacity: 1;
  transform: scale(1.1);
}

.toggle-text {
  font-size: 0.95rem;
  font-weight: 500;
  opacity: 0.9;
  transition: opacity 0.2s ease;
}

.sidebar-toggle:hover .toggle-text {
  opacity: 1;
}

.loading-text {
  margin-top: 2rem;
  font-size: 1rem;
  color: v-bind('isDarkMode ? "var(--dark-text-primary)" : "var(--light-text-primary)"');
  text-align: center;
  animation: fadeIn 0.3s ease-out;
  opacity: 0.8;
}
</style>

