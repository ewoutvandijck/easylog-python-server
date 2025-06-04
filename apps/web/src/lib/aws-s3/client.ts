import { S3Client } from '@aws-sdk/client-s3';

import serverConfig from '@/server.config';

const s3Client = new S3Client({
  endpoint: serverConfig.s3Endpoint,
  region: serverConfig.s3Region,
  credentials: {
    accessKeyId: serverConfig.s3AccessKey,
    secretAccessKey: serverConfig.s3SecretKey
  },
  forcePathStyle: true
});

export default s3Client;
