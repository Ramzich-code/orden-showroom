import type { NextConfig } from "next";

// Static export (GitHub Pages). NEXT_PUBLIC_BASE_PATH is the repo sub-path
// in the Pages build, empty in local dev.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || undefined;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  basePath,
  images: { unoptimized: true },
};

export default nextConfig;
