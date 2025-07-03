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
  BETTER_AUTH_SECRET: process.env.BETTER_AUTH_SECRET,
  EASYLOG_DB_HOST: process.env.EASYLOG_DB_HOST,
  EASYLOG_DB_PORT: process.env.EASYLOG_DB_PORT,
  EASYLOG_DB_USER: process.env.EASYLOG_DB_USER,
  EASYLOG_DB_NAME: process.env.EASYLOG_DB_NAME,
  EASYLOG_DB_PASSWORD: process.env.EASYLOG_DB_PASSWORD,
  BLOB_READ_WRITE_TOKEN: process.env.BLOB_READ_WRITE_TOKEN,
  MISTRAL_API_KEY: process.env.MISTRAL_API_KEY
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
  BETTER_AUTH_SECRET: z.string(),
  EASYLOG_DB_HOST: z.string(),
  EASYLOG_DB_PORT: z.string().transform((val) => parseInt(val)),
  EASYLOG_DB_USER: z.string(),
  EASYLOG_DB_NAME: z.string(),
  EASYLOG_DB_PASSWORD: z.string(),
  BLOB_READ_WRITE_TOKEN: z.string(),
  MISTRAL_API_KEY: z.string()
});

const serverEnv = envSchema.parse(rawEnv);

export default serverEnv;
