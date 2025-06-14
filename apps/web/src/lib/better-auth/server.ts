import { betterAuth } from 'better-auth';
import { drizzleAdapter } from 'better-auth/adapters/drizzle';
import { nextCookies } from 'better-auth/next-js';
import { genericOAuth } from 'better-auth/plugins';

import db from '@/database/client';
import * as schema from '@/database/schema';
import serverConfig from '@/server.config';

const authServerClient = betterAuth({
  baseURL: serverConfig.appUrl.toString(),
  secret: serverConfig.betterAuthSecret,
  plugins: [
    nextCookies(),
    genericOAuth({
      config: [
        {
          providerId: 'easylog',
          clientId: '99a0db85-5cd0-4f60-b65e-03483b72d14a',
          discoveryUrl:
            'https://staging2.easylog.nu/.well-known/openid-configuration',
          scopes: ['openid'],
          pkce: true,
          clientSecret: ''
        }
      ]
    })
  ],
  advanced: {
    database: {
      generateId: () => crypto.randomUUID()
    }
  },
  database: drizzleAdapter(db, {
    provider: 'pg',
    usePlural: true,
    schema
  })
});

export default authServerClient;
