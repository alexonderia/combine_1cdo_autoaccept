import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const isDocker = process.env.BUILD_ENV === "docker";

export default defineConfig({
  plugins: [react()],
  base: "/",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8001"
    },
  },
  build: {
    emptyOutDir: true,
    outDir: isDocker ? "dist" : "../backend/static",
  },

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
