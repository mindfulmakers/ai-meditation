import react from "@vitejs/plugin-react-swc";
import path from "path";
import { defineConfig } from "vite";

const s3Name = "ai-meditation-starter-kit-react";
const useCdnBase = process.env.VITE_USE_CDN === "true";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 5173,
  },
  base: useCdnBase ? `https://cdn.openbase.app/${s3Name}/` : "/",
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    globals: true,
    clearMocks: true,
  },
}));
