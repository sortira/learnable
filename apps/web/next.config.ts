import type { NextConfig } from "next";

const internalApiUrl = process.env.LEARNABLE_INTERNAL_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${internalApiUrl}/api/:path*`
      }
    ];
  }
};

export default nextConfig;
