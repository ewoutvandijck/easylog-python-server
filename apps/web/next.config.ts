import type { NextConfig } from 'next';

import serverEnv from '@/server.env';

const nextConfig: NextConfig = {
  rewrites: async () => {
    return [
      {
        source: '/s3/:path*',
        destination: `${serverEnv.S3_ENDPOINT}/:path*`
      }
    ];
  }
};

export default nextConfig;
