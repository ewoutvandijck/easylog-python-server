import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { nextCookies } from 'better-auth/next-js';
import { passkey } from 'better-auth/plugins/passkey';
import { eq } from 'drizzle-orm';

import slugify from '@/app/_ui/utils/slugify';
import db from '@/database/client';
import * as schema from '@/database/schema';
import serverConfig from '@/server.config';

const authServerClient = betterAuth({
  baseURL: serverConfig.appUrl.toString(),
  secret: serverConfig.betterAuthSecret,
  plugins: [nextCookies(), passkey()],
  advanced: {
    database: {
      generateId: () => crypto.randomUUID()
    }
  },
  database: drizzleAdapter(db, {
    provider: 'pg',
    usePlural: true,
    schema
  }),
  emailAndPassword: {
    enabled: true
  },
  socialProviders: {
    google: {
      clientId: serverConfig.googleOauthClientId,
      clientSecret: serverConfig.googleOauthClientSecret
    }
  }
});

export default authServerClient;
