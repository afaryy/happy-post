import type { NextConfig } from "next";

const backendBaseUrl = process.env.BACKEND_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/api/:path*`
      }
    ];
  }
};

export default nextConfig;
