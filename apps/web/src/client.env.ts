import { z } from 'zod';

const rawEnv = {
  NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  NEXT_PUBLIC_VERCEL_URL: process.env.NEXT_PUBLIC_VERCEL_URL
};

const envSchema = z.object({
  NEXT_PUBLIC_APP_URL: z.string().optional(),
  NEXT_PUBLIC_VERCEL_URL: z.string().optional()
});

const clientEnv = envSchema.parse(rawEnv);

export default clientEnv;
