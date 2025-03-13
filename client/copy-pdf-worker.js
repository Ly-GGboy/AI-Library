import { copyFileSync, mkdirSync } from 'fs'
import { dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

// 创建目标目录
mkdirSync('public', { recursive: true })
mkdirSync('public/pdf', { recursive: true })

// 复制 worker 文件
const workerPath = resolve(__dirname, 'node_modules/pdfjs-dist/build/pdf.worker.min.js')
const targetPath = resolve(__dirname, 'public/pdf/pdf.worker.min.js')

try {
  copyFileSync(workerPath, targetPath)
  console.log('PDF.js worker file copied successfully')
} catch (error) {
  console.error('Error copying PDF.js worker file:', error)
  process.exit(1)
} 