import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  webpack(config, { dev }) {
    // Browser verification can run on storage-constrained development machines.
    if (dev && process.env.SAFETYLENS_DISABLE_BUILD_CACHE === "true") config.cache = false;
    return config;
  },
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
