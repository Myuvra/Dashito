import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sites } from '@openai/sites-vite-plugin'

export default defineConfig(async () => {
  process.env.WRANGLER_WRITE_LOGS ??= 'false'
  process.env.WRANGLER_LOG_PATH ??= '.wrangler/logs'
  process.env.MINIFLARE_REGISTRY_PATH ??= '.wrangler/registry'
  const { cloudflare } = await import('@cloudflare/vite-plugin')

  return {
    base: './',
    plugins: [
      react(),
      sites(),
      cloudflare({
        viteEnvironment: { name: 'server' },
        config: {
          main: './worker/index.js',
          compatibility_date: '2026-05-22',
          compatibility_flags: ['nodejs_compat'],
          assets: {
            binding: 'ASSETS',
            not_found_handling: 'single-page-application',
          },
        },
      }),
    ],
  }
})
