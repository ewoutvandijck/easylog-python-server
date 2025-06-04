import { inferRouterOutputs } from '@trpc/server';

import { createTRPCRouter } from '@/lib/trpc/trpc';

import authRouter from './app/_auth/router';
import documentsRouter from './app/_documents/router';
import organizationsRouter from './app/_organizations/router';

export const appRouter = createTRPCRouter({
  auth: authRouter,
  organizations: organizationsRouter,
  documents: documentsRouter
});

export type AppRouter = typeof appRouter;

export type RouterOutputs = inferRouterOutputs<AppRouter>;
