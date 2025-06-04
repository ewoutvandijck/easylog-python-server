import { z } from 'zod';

import organizationMiddleware from '@/app/_organizations/middleware/organizationMiddleware';
import { ingestDocumentJob } from '@/jobs/ingest-document/ingest-document-job';

const documentsBatchProcess = organizationMiddleware
  .input(
    z.object({
      filePaths: z.array(z.string())
    })
  )
  .mutation(
    async ({
      input: { filePaths },
      ctx: {
        organization: { id: organizationId }
      }
    }) => {
      await ingestDocumentJob.batchTrigger(
        filePaths.map((filePath) => ({
          payload: {
            organizationId,
            filename: filePath
          },
          tags: [`org_${organizationId}`]
        }))
      );
    }
  );

export default documentsBatchProcess;
