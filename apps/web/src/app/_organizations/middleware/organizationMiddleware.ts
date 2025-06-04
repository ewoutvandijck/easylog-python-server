import { TRPCError } from '@trpc/server';
import { z } from 'zod';

import db from '@/database/client';
import { protectedProcedure } from '@/lib/trpc/procedures';
import isUUID from '@/utils/is-uuid';

const organizationMiddleware = protectedProcedure
  .input(
    z.object({
      organizationId: z.string()
    })
  )
  .use(async ({ next, ctx, input }) => {
    const organization = await db.query.organizations.findFirst({
      where: {
        [isUUID(input.organizationId) ? 'id' : 'slug']: input.organizationId
      }
    });

    if (!organization) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Organization not found'
      });
    }

    return next({
      ctx: {
        ...ctx,
        organization
      }
    });
  });

export default organizationMiddleware;
