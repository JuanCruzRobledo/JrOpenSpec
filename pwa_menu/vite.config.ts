import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    // TailwindCSS 4 via Vite plugin (CSS-first, no tailwind.config.ts)
    tailwindcss(),

    // React with babel-plugin-react-compiler enabled
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {}],
        ],
      },
    }),

    // PWA configuration with Workbox runtime caching
    VitePWA({
      // 'prompt' mode: shows update notification instead of auto-reloading
      registerType: 'prompt',

      // Include additional assets in precache
      includeAssets: ['favicon.svg', 'icon-192x192.png', 'icon-512x512.png'],

      manifest: {
        name: 'Menú Digital',
        short_name: 'Menú',
        description: 'Menú digital del restaurante con filtrado de alérgenos',
        theme_color: '#f97316',
        background_color: '#0a0a0a',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icon-192x192-maskable.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'maskable',
          },
          {
            src: '/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icon-512x512-maskable.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },

      workbox: {
        // SPA: navigate fallback to index.html for offline shell
        navigateFallback: '/index.html',

        // Exclude API calls and non-HTML navigation from navigate fallback
        navigateFallbackDenylist: [/^\/api\//],

        runtimeCaching: [
          // CacheFirst 30 days: local images and CDN images
          // Serves instantly from cache, ideal for product photos
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|avif|ico)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache-v1',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },

          // NetworkFirst 5s timeout: public menu API endpoints
          // Tries network, falls back to cache if network exceeds 5s or is offline
          {
            urlPattern: /^https?:\/\/[^/]+\/api\/public\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-public-cache-v1',
              networkTimeoutSeconds: 5,
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 5, // 5 minutes max cache age
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },

          // StaleWhileRevalidate 1 year: Google Fonts and web fonts
          // Serves from cache immediately, revalidates in background
          {
            urlPattern: /^https:\/\/fonts\.(?:googleapis|gstatic)\.com\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'google-fonts-cache-v1',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },

          // StaleWhileRevalidate: i18n locale JSON files
          // Menu loads fast even offline, background refresh on network
          {
            urlPattern: /\/locales\/[a-z]{2}\/[a-z]+\.json$/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'i18n-cache-v1',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 60 * 24, // 1 day
              },
            },
          },
        ],
      },
    }),
  ],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: 5176,
    strictPort: true,
  },

  preview: {
    port: 5176,
    strictPort: true,
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    css: true,
  },
});
