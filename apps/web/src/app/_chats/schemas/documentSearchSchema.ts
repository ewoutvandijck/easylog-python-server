import { z } from 'zod';

const documentSearchSchema = z.object({
  status: z.enum([
    'searching_documents',
    'documents_found',
    'researching_document',
    'document_research_complete'
  ]),
  content: z.string()
});

export type DocumentSearch = z.infer<typeof documentSearchSchema>;

export default documentSearchSchema;
