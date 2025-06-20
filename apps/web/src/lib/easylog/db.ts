import { drizzle } from 'drizzle-orm/mysql2';

import serverConfig from '@/server.config';

const easylogDb = drizzle({
  connection: {
    host: serverConfig.easylogDbHost,
    port: serverConfig.easylogDbPort,
    user: serverConfig.easylogDbUser,
    password: serverConfig.easylogDbPassword,
    database: serverConfig.easylogDbName
  }
});

export default easylogDb;
