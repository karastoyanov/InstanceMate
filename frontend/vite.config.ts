import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Read .env from the repo root instead of frontend/ - one env file for
  // the whole project (backend, frontend, mcp-server, infra).
  envDir: '..',
})
