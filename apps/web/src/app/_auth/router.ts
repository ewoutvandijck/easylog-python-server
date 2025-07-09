import { createTRPCRouter } from '@/lib/trpc/trpc';

import authGetMe from './controllers/authGetMe';

const authRouter = createTRPCRouter({
  getMe: authGetMe
});

export default authRouter;
