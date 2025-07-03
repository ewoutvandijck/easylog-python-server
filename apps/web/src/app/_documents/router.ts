import { createTRPCRouter } from '@/lib/trpc/trpc';

import documentsGetMany from './controllers/documentsGetMany';

const documentsRouter = createTRPCRouter({
  getMany: documentsGetMany
});

export default documentsRouter;
