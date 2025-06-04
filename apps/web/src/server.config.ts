import serverEnv from './server.env';
import getAppUrl from './utils/get-app-url';

const serverConfig = {
  env: serverEnv.NODE_ENV,
  appUrl: getAppUrl(),
  dbUrl: serverEnv.DB_URL,
  openrouterApiKey: serverEnv.OPENROUTER_API_KEY,
  s3Endpoint: serverEnv.S3_ENDPOINT,
  s3Region: serverEnv.S3_REGION,
  s3AccessKey: serverEnv.S3_ACCESS_KEY,
  s3SecretKey: serverEnv.S3_SECRET_KEY,
  s3PublicBucketName: serverEnv.S3_PUBLIC_BUCKET_NAME,
  triggerSecretKey: serverEnv.TRIGGER_SECRET_KEY,
  betterAuthSecret: serverEnv.BETTER_AUTH_SECRET
} as const;

export default serverConfig;
