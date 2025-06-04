import { passkeyClient } from 'better-auth/client/plugins';
import { createAuthClient } from 'better-auth/react';

import clientConfig from '@/client.config';

const authBrowserClient = createAuthClient({
  baseURL: clientConfig.appUrl.toString(),
  plugins: [passkeyClient()]
});

export default authBrowserClient;
