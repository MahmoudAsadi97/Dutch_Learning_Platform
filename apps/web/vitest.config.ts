import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Component and hook tests (`npm run test:component`) run in jsdom with React Testing Library.
 * The pure-module tests in tests/unit keep running on node:test (`npm run test:unit`).
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    include: ["tests/component/**/*.test.{ts,tsx}"],
    setupFiles: ["tests/component/setup.ts"],
    css: false,
  },
});
