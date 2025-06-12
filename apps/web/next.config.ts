import type { NextConfig } from 'next';

import serverEnv from '@/server.env';

const nextConfig: NextConfig = {
  allowedDevOrigins: ['*.ngrok.app', '*.ngrok.ngrok.dev'],
  rewrites: async () => {
    return [
      {
        source: '/s3/:path*',
        destination: `${serverEnv.S3_ENDPOINT}/:path*`
      }
    ];
  },
  redirects: async () => {
    return [
      {
        source: '/',
        destination: '/chat',
        permanent: false
      }
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'ui-avatars.com'
      }
    ]
  }
};

export default nextConfig;
