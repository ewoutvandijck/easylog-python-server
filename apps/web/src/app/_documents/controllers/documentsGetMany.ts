import organizationMiddleware from '@/app/_organizations/middleware/organizationMiddleware';
import db from '@/database/client';

const documentsGetMany = organizationMiddleware.query(async ({ ctx }) => {
  return await db.query.documents.findMany({
    where: {
      organizationId: ctx.organization.id
    },
    columns: {
      id: true,
      path: true,
      type: true,
      summary: true,
      tags: true,
      createdAt: true,
      updatedAt: true
    }
  });
});

export default documentsGetMany;
