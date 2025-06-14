import { drizzle } from 'drizzle-orm/postgres-js';

import serverConfig from '@/server.config';

import relations from './relations';

const db = drizzle(serverConfig.dbUrl, {
  relations
});

export default db;
