import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icon.svg", "ocr/**/*"],
      manifest: {
        name: "Vehicle Maintenance Planner",
        short_name: "Vehicle Maint",
        description: "Private, offline estimate and quote decision support.",
        theme_color: "#163c3a",
        background_color: "#f4f0e6",
        display: "standalone",
        start_url: "/",
        scope: "/",
        icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" }],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,wasm,gz}"],
        maximumFileSizeToCacheInBytes: 15 * 1024 * 1024,
        navigateFallback: "/index.html",
        runtimeCaching: [],
      },
      devOptions: { enabled: true },
    }),
  ],
  test: {
    environment: "jsdom",
    coverage: {
      provider: "v8",
      reporter: ["text"],
      include: ["src/decision.ts", "src/crypto.ts", "src/packet.ts"],
      thresholds: { lines: 90, functions: 90, statements: 90, branches: 80 },
    },
  },
});
