import { createTRPCRouter } from '@/lib/trpc/trpc';

import documentsBatchProcess from './controllers/documentsBatchProcess';
import documentsCreateUploadUrls from './controllers/documentsCreateUploadUrls';
import documentsGetMany from './controllers/documentsGetMany';

const documentsRouter = createTRPCRouter({
  getMany: documentsGetMany,
  createUploadUrls: documentsCreateUploadUrls,
  batchProcess: documentsBatchProcess
});

export default documentsRouter;
