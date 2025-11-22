/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    unoptimized: true, // For static export or when image optimization isn't needed
  },
}

module.exports = nextConfig

