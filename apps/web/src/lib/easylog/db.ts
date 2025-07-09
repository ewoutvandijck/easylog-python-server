import { drizzle } from 'drizzle-orm/mysql2';
import mysql from 'mysql2/promise';

import serverConfig from '@/server.config';

const connection = await mysql.createConnection({
  host: serverConfig.easylogDbHost,
  port: serverConfig.easylogDbPort,
  user: serverConfig.easylogDbUser,
  password: serverConfig.easylogDbPassword,
  database: serverConfig.easylogDbName
});

const easylogDb = drizzle({ client: connection });

export default easylogDb;
