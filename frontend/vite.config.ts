import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: process.env.CYPRESS_COVERAGE === 'true' ? [['istanbul', {
          extension: ['.js', '.jsx', '.ts', '.tsx']
        }]] : []
      }
    }),
    tailwindcss(),
  ],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('@mui')) return 'mui-vendor';
            if (id.includes('recharts')) return 'recharts-vendor';
            if (id.includes('lucide-react')) return 'lucide-vendor';
            if (id.includes('@radix-ui')) return 'radix-vendor';
            return 'vendor';
          }
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    port: 3000,
    host: '0.0.0.0',
    open: false,
    // Allow ngrok and other tunnel hosts (Vite 6 blocks unknown Host headers by default).
    allowedHosts: ['.ngrok-free.dev', '.ngrok.io', '.ngrok.app'],
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_PROXY_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
      ignored: [
        '**/node_modules/**',
        '**/.pnpm-store/**',
        '**/.next/**',
        '**/dist/**',
        '**/.git/**',
        '**/playwright-report/**',
        '**/test-results/**',
      ],
    },
  },
});
