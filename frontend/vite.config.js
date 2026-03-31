import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Use root for local dev, repository name for GitHub Pages build
  base: command === 'build' ? '/Deepfake-Detaction/' : '/',
}))
