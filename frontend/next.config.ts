import path from "node:path";
import type { NextConfig } from "next";

// content/ lives next to frontend/, so the bundler root must include the repository root.
const repositoryRoot = path.resolve(process.cwd(), "..");

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    root: repositoryRoot,
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  outputFileTracingRoot: repositoryRoot,
};

export default nextConfig;
