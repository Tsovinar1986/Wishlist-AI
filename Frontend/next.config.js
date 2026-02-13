/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Allow dev server access from other devices on the network (e.g. http://192.168.x.x:3000)
  allowedDevOrigins: ["http://192.168.27.7:3000", "http://localhost:3000"],
};

module.exports = nextConfig;
