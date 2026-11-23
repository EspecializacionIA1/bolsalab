import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

const base: NextConfig = {
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default function config(phase: string): NextConfig {
  if (phase === PHASE_DEVELOPMENT_SERVER) {
    return {
      ...base,
      rewrites: async () => [
        { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      ],
    };
  }

  return { ...base, output: "export", trailingSlash: true };
}
