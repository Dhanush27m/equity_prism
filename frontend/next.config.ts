// Component: Frontend -> Build config -> Next.js configuration
// Belongs to: read by the Next.js dev server and build (`next dev` / `next build`).
// Purpose: proxies /api/* requests to the FastAPI backend during local development
// (BACKEND_URL defaults to localhost:8000) so the frontend can call relative /api paths
// without CORS during dev. In the deployed profile the frontend instead calls the
// backend by absolute URL (NEXT_PUBLIC_API_BASE, see lib/api.ts) and this rewrite is
// effectively unused, since Vercel and Render are different origins.
import path from "path";
import type { NextConfig } from "next";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
    ];
  },
};

export default nextConfig;
