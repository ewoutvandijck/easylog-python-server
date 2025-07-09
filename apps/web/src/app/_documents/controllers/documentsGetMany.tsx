import { eq } from 'drizzle-orm';
import { z } from 'zod';

import db from '@/database/client';
import { documents } from '@/database/schema';
import { protectedProcedure } from '@/lib/trpc/procedures';

const documentsGetMany = protectedProcedure
  .input(
    z.object({
      cursor: z.number().default(0),
      limit: z.number().min(1).max(100).default(10)
    })
  )
  .query(async ({ input, ctx }) => {
    const [data, total] = await Promise.all([
      db.query.documents.findMany({
        limit: input.limit,
        offset: input.cursor,
        orderBy: {
          createdAt: 'desc'
        },
        where: {
          userId: ctx.user.id
        }
      }),
      db.$count(documents, eq(documents.userId, ctx.user.id))
    ]);

    return {
      data,
      meta: {
        total,
        cursor: input.cursor + input.limit,
        limit: input.limit
      }
    };
  });

export default documentsGetMany;
