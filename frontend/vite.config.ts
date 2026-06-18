import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server:
  {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts:
    [
      'oj.askryggdrasil.top',
      '.askryggdrasil.top',
    ],
    proxy:
    {
      '/api':
      {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})