import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Rewrites only active in development (production uses NEXT_PUBLIC_API_BASE_URL)
  ...(process.env.NODE_ENV === "development" || !process.env.NEXT_PUBLIC_API_BASE_URL
    ? {
        async rewrites() {
          return [
            {
              source: "/api/:path*",
              destination: "http://127.0.0.1:8000/api/:path*",
            },
          ];
        },
      }
    : {}),
};

export default nextConfig;