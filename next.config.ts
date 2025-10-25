import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export", // This exports static HTML/JS files
  images: {
    unoptimized: true, // Required for static export
  },
  async rewrites() {
    const target = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    return [
      { source: "/api/:path*", destination: `${target}/api/:path*` },
      { source: "/health", destination: `${target}/health` },
    ];
  },
};

export default nextConfig;
