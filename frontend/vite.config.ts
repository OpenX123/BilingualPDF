import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../pdf2zh_next/frontend_dist"),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:7861",
      "/admin/api": "http://127.0.0.1:7861",
      "/admin/login": "http://127.0.0.1:7861",
      "/admin/logout": "http://127.0.0.1:7861"
    }
  }
});
