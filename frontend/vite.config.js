import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react()
  ],
  base: '/',
  build: {
    outDir: 'dist',
    sourcemap: true,
    // Optimize bundle size
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@heroicons/react', 'react-hot-toast'],
          'editor-vendor': ['@monaco-editor/react'],
          'chart-vendor': ['recharts'],
          'utils': ['axios', 'date-fns', 'uuid']
        }
      }
    },
    // Reduce chunk size warnings threshold
    chunkSizeWarningLimit: 1000,
    // Minification options
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
    exclude: ['@monaco-editor/react']
  }
})
