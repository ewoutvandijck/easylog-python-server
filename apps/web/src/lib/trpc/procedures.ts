import { TRPCError } from '@trpc/server';
import { experimental_nextAppDirCaller } from '@trpc/server/adapters/next-app-dir';

import createTRPCContext from './context';
import { t } from './trpc';

/**
 * Public (unauthed) procedure
 *
 * This is the base piece you use to build new queries and mutations on your
 * tRPC API. It does not guarantee that a user querying is authorized, but you
 * can still access user session data if they are logged in
 */
export const publicProcedure = t.procedure;

/**
 * Protected (authenticated) procedure
 *
 * If you want a query or mutation to ONLY be accessible to logged in users, use
 * this. It verifies the session is valid and guarantees `ctx.session.user` is
 * not null.
 *
 * @see https://trpc.io/docs/procedures
 */
export const protectedProcedure = t.procedure.use(async ({ ctx, next }) => {
  if (!ctx.user) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'You are not authorized to access this resource'
    });
  }

  return next({
    ctx: {
      ...ctx,
      user: ctx.user
    }
  });
});

/**
 * Server action procedure
 *
 * This is a procedure that is used to call server actions. If you need access
 * to redirecting, cookies, or other server action specific functionality, use
 * this. Only for mutations.
 */
export const serverActionProcedure = t.procedure
  .experimental_caller(
    experimental_nextAppDirCaller({
      createContext: createTRPCContext
    })
  )
  .use(async ({ ctx, next }) => {
    if (!ctx.user) {
      throw new TRPCError({
        code: 'UNAUTHORIZED',
        message: 'You are not authorized to access this resource'
      });
    }

    return next({
      ctx: {
        ...ctx,
        user: ctx.user
      }
    });
  });
