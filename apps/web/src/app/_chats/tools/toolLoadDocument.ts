import { tool } from 'ai';
import { z } from 'zod';

import db from '@/database/client';

const getToolLoadDocument = () => {
  return tool({
    description: 'Load a document into the knowledge base',
    inputSchema: z.object({
      documentId: z.string().describe('The ID of the document to load')
    }),
    execute: async ({ documentId }) => {
      const document = await db.query.documents.findFirst({
        where: {
          id: documentId
        }
      });

      if (!document) {
        throw new Error('Document not found');
      }

      return JSON.stringify(document);
    }
  });
};

export default getToolLoadDocument;
