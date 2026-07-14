const nextConfig = {
  distDir: process.env.NEXT_DIST_DIR || ".next",
  async rewrites() {
    const backendUrl = process.env.BACKEND_PROXY_URL || "http://191.44.87.38:8000";

    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // Windows file locking can make Next's filesystem cache emit noisy
    // snapshot warnings even when the build succeeds.
    config.cache = false;
    return config;
  },
};

export default nextConfig;
