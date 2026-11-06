import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import node from '@astrojs/node';

// Servidor Astro con soporte para API endpoints (Gemini AI & Reversionador de URLs)
export default defineConfig({
  site: process.env.PUBLIC_SITE_URL || 'https://example.com',
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  trailingSlash: 'never',
  integrations: [sitemap()],
  markdown: {
    shikiConfig: { theme: 'github-dark' },
  },
  build: {
    inlineStylesheets: 'auto',
  },
});
