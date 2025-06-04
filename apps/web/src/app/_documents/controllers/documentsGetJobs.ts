import { auth, runs } from '@trigger.dev/sdk';

import organizationMiddleware from '@/app/_organizations/middleware/organizationMiddleware';
import { ingestDocumentJob } from '@/jobs/ingest-document/ingest-document-job';

const documentsGetJobs = organizationMiddleware.query(async ({ ctx }) => {
  const allRuns = await runs.list({
    tag: `org_${ctx.organization.id}`,
    taskIdentifier: ingestDocumentJob.id,
    status: ['QUEUED', 'EXECUTING', 'REATTEMPTING']
  });

  const accessToken = await auth.createPublicToken({
    scopes: {
      read: {
        runs: allRuns.data.map((run) => run.id)
      }
    }
  });

  return {
    accessToken,
    runIds: allRuns.data.map((run) => run.id)
  };
});

export default documentsGetJobs;
