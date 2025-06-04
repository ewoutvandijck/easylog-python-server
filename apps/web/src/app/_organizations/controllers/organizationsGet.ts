import { TRPCError } from '@trpc/server';
import { z } from 'zod';

import db from '@/database/client';
import { protectedProcedure } from '@/lib/trpc/procedures';
import isUUID from '@/utils/is-uuid';

const organizationsGet = protectedProcedure
  .input(
    z.object({
      organizationId: z.string()
    })
  )
  .query(async ({ input }) => {
    const { organizationId } = input;

    const organization = await db.query.organizations.findFirst({
      where: {
        [isUUID(organizationId) ? 'id' : 'slug']: organizationId
      }
    });

    if (!organization) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Organization not found'
      });
    }

    return organization;
  });

export default organizationsGet;
