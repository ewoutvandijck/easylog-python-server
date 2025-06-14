import type { Config } from 'drizzle-kit';

import serverConfig from '@/server.config';

export default {
  schema: './src/database/schema.ts',
  out: './src/database',
  dialect: 'postgresql',
  dbCredentials: {
    url: serverConfig.dbUrl
  }
} satisfies Config;
