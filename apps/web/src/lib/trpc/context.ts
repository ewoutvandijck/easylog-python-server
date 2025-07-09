import { headers } from 'next/headers';
import { cache } from 'react';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';

const createTRPCContext = cache(async () => {
  return {
    user: await getCurrentUser(await headers())
  };
});

export type Context = Awaited<ReturnType<typeof createTRPCContext>>;

export default createTRPCContext;
