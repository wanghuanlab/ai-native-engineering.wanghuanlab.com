import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { trainingAssets } from "./scripts/training-assets";

export default defineConfig({
  plugins: [vue(), trainingAssets()],
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
  build: { target: "es2022" },
});
