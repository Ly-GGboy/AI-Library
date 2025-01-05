import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    https: {
      key: fs.readFileSync(path.resolve(__dirname, '../server/key.pem')),
      cert: fs.readFileSync(path.resolve(__dirname, '../server/cert.pem')),
    },
    proxy: {
      '/api': {
        target: 'https://localhost:8000',
        secure: false,  // 因为我们用的是自签名证书
        changeOrigin: true,
        ws: true,  // 支持 WebSocket
      }
    }
  },
})
