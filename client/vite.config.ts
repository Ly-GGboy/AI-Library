import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'
import { visualizer } from 'rollup-plugin-visualizer'
import viteCompression from 'vite-plugin-compression'
import fs from 'node:fs'
import path from 'node:path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // 生成gzip压缩文件
    viteCompression({
      verbose: true,
      disable: false,
      threshold: 10240,
      algorithm: 'gzip',
      ext: '.gz',
    }),
    // 生成构建分析报告
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    }
  },
  build: {
    // 启用多页面构建
    rollupOptions: {
      output: {
        manualChunks: {
          'pdf.worker': ['pdfjs-dist/build/pdf.worker.min'],
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['@heroicons/vue'],
          'markdown': ['marked', 'highlight.js'],
          'utils': ['axios', 'lodash-es']
        },
        // 自定义chunk文件名
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      }
    },
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 禁用源码映射以减小构建体积
    sourcemap: false,
    // 减小chunk大小警告阈值
    chunkSizeWarningLimit: 1000,
    // 启用minify
    minify: 'terser',
    // terser配置
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    // 启用CSS压缩
    cssMinify: true,
    // 启用预加载
    assetsInlineLimit: 4096,
  },
  server: {
    https: {
      key: fs.readFileSync(path.resolve(process.cwd(), '../certs/key.pem')),
      cert: fs.readFileSync(path.resolve(process.cwd(), '../certs/cert.pem')),
    },
    proxy: {
      '/api': {
        target: 'https://frp6.mmszxc.xin:18926/',
        changeOrigin: true,
        ws: true,
        secure: false 
      }
    }
  },
  // 优化预构建
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'marked',
      'prismjs',
      '@heroicons/vue/24/outline'
    ],
    exclude: ['pdfjs-dist/build/pdf.worker.min']
  }
})
