import { z } from 'zod';

const rawEnv = {
  NODE_ENV: process.env.NODE_ENV,
  DB_URL: process.env.DB_URL,
  OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
  S3_ENDPOINT: process.env.S3_ENDPOINT,
  S3_REGION: process.env.S3_REGION,
  S3_ACCESS_KEY: process.env.S3_ACCESS_KEY,
  S3_SECRET_KEY: process.env.S3_SECRET_KEY,
  S3_PUBLIC_BUCKET_NAME: process.env.S3_PUBLIC_BUCKET_NAME,
  TRIGGER_SECRET_KEY: process.env.TRIGGER_SECRET_KEY,
  BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET
};

const envSchema = z.object({
  NODE_ENV: z
    .union([
      z.literal('development'),
      z.literal('preview'),
      z.literal('production'),
      z.literal('test')
    ])
    .default('development'),
  DB_URL: z.string(),
  OPENROUTER_API_KEY: z.string(),
  S3_ENDPOINT: z.string().default('http://localhost:9000'),
  S3_REGION: z.string().default('us-east-1'),
  S3_ACCESS_KEY: z.string().default('miniouser'),
  S3_SECRET_KEY: z.string().default('miniopassword123'),
  S3_PUBLIC_BUCKET_NAME: z.string().default('public-storage'),
  TRIGGER_SECRET_KEY: z.string(),
  BETTER_AUTH_SECRET: z.string()
});

const serverEnv = envSchema.parse(rawEnv);

export default serverEnv;
