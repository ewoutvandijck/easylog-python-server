import { createTRPCRouter } from '@/lib/trpc/trpc';

import chatsGetOrCreate from './controllers/chatsGetOrCreate';

const chatsRouter = createTRPCRouter({
  getOrCreate: chatsGetOrCreate
});

export default chatsRouter;
