import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  webpack(config) {
    // Browser verification can run on storage-constrained development machines.
    if (process.env.SAFETYLENS_DISABLE_BUILD_CACHE === "true") config.cache = false;
    return config;
  },
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
