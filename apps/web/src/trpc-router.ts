import { inferRouterOutputs } from '@trpc/server';

import { createTRPCRouter } from '@/lib/trpc/trpc';

import authRouter from './app/_auth/router';

export const appRouter = createTRPCRouter({
  auth: authRouter
});

export type AppRouter = typeof appRouter;

export type RouterOutputs = inferRouterOutputs<AppRouter>;
