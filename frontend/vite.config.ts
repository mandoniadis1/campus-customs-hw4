import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
// In development, /api and /images are forwarded to the FastAPI backend
// (run from backend/: uvicorn main:app --reload --port 8000). Override with BACKEND_URL if needed.
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174, // 5173 is used by another class project on this machine
    strictPort: true,
    proxy: {
      '/api': backend,
      '/images': backend,
    },
  },
})
