import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: ['babel-plugin-react-compiler'],
      },
    }),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5177,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          // Split vendor chunks for better caching
          if (id.includes('node_modules')) {
            if (id.includes('react-router')) return 'router';
            if (id.includes('axios')) return 'http';
          }
          return undefined;
        },
      },
    },
  },
});
