import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Get API port from environment or default to 8000
const apiPort = process.env.API_PORT || '8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: `http://localhost:${apiPort}`,
        changeOrigin: true,
      },
    },
  },
})