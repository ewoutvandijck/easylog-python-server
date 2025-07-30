import { TRPCError } from '@trpc/server';
import { z } from 'zod';

import db from '@/database/client';
import { protectedProcedure } from '@/lib/trpc/procedures';
import isUUID from '@/utils/is-uuid';

const agentMiddleware = protectedProcedure
  .input(
    z.object({
      agentId: z.string()
    })
  )
  .use(async ({ next, ctx, input }) => {
    const agent = await db.query.agents.findFirst({
      where: {
        [isUUID(input.agentId) ? 'id' : 'slug']: input.agentId
      }
    });

    if (!agent) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Agent not found'
      });
    }

    return next({
      ctx: {
        ...ctx,
        agent
      }
    });
  });

export default agentMiddleware;
