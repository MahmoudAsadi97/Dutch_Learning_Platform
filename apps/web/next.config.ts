import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // The container image (Phase B) builds with NEXT_OUTPUT=standalone; `next start` on a laptop does not support it.
  ...(process.env.NEXT_OUTPUT === "standalone" ? { output: "standalone" as const } : {}),
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "same-origin" },
          { key: "Permissions-Policy", value: "microphone=(self), camera=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
