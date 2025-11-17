import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  root: 'web',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'web/index.html'),
        rag: resolve(__dirname, 'web/rag_interface.html'),
        data: resolve(__dirname, 'web/data_viewer.html'),
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'web/src'),
      '@components': resolve(__dirname, 'web/src/components'),
      '@pages': resolve(__dirname, 'web/src/pages'),
      '@utils': resolve(__dirname, 'web/src/utils'),
      '@hooks': resolve(__dirname, 'web/src/hooks'),
      '@types': resolve(__dirname, 'web/src/types'),
    },
  },
})