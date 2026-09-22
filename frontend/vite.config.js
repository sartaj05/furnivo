import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './src/tests/setup.js',
    coverage: { reporter: ['text', 'html'], thresholds: { lines: 5, functions: 2, branches: 5, statements: 5 } },
  },
})
