import 'server-only';

import { createTRPCOptionsProxy } from '@trpc/tanstack-react-query';

import getQueryClient from '@/lib/react-query';
import { appRouter } from '@/trpc-router';

import createTRPCContext from './context';

const api = createTRPCOptionsProxy({
  ctx: () => createTRPCContext(),
  router: appRouter,
  queryClient: getQueryClient
});

export default api;
