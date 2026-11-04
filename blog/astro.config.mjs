import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Blog 100% estático generado por el backend Python (FastAPI)
export default defineConfig({
  site: process.env.PUBLIC_SITE_URL || 'https://example.com',
  output: 'static',
  trailingSlash: 'never',
  integrations: [sitemap()],
  markdown: {
    shikiConfig: { theme: 'github-dark' },
  },
  build: {
    inlineStylesheets: 'auto',
  },
});
