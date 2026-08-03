import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    coverage: {
      exclude: [
        ".next/**",
        "next-env.d.ts",
        "vitest.config.mts",
        "vitest.setup.ts"
      ],
      provider: "v8",
      reporter: ["text", "lcov"]
    },
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"]
  }
});
