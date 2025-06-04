import { createTRPCRouter } from '@/lib/trpc/trpc';

import organizationsGet from './controllers/organizationsGet';

const organizationsRouter = createTRPCRouter({
  get: organizationsGet
});

export default organizationsRouter;
