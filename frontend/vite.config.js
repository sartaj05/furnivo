import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Keep Vite/Vitest caches in the project workspace. Some managed Windows
  // environments deny writes to node_modules, which otherwise makes build and
  // test results depend on the machine rather than the repository.
  cacheDir: './.vite-cache',
  test: {
    environment: 'jsdom',
    setupFiles: './src/tests/setup.js',
    coverage: {
      reporter: ['text', 'html'],
      reportsDirectory: './.coverage',
      thresholds: { lines: 5, functions: 2, branches: 4, statements: 5 },
    },
  },
})
