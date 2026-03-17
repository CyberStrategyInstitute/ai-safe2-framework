import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ai-safe2-framework/dashboard/', // <-- GitHub Pages subpath
})
