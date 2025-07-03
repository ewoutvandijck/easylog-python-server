import { UIMessageStreamWriter, generateObject, generateText, tool } from 'ai';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

import db from '@/database/client';
import openrouterProvider from '@/lib/ai-providers/openrouter';
import splitArrayBatches from '@/utils/split-array-batches';

const getToolSearchKnowledgeBase = (
  messageStreamWriter: UIMessageStreamWriter
) => {
  console.log('🔍 [toolSearchKnowledgeBase] Tool function created');

  return tool({
    description: 'Search the knowledge base for information',
    inputSchema: z.object({
      userSearchQuery: z.string().describe('The question the user asked')
    }),
    execute: async ({ userSearchQuery }) => {
      const id = uuidv4();

      console.log(userSearchQuery);

      messageStreamWriter.write({
        type: 'data-document-search',
        id,
        data: {
          status: 'searching_documents',
          content: `Searching relevant knowledge base documents for "${userSearchQuery}"`
        }
      });

      const dbDocuments = await db.query.documents.findMany({
        limit: 50,
        columns: {
          id: true,
          name: true,
          summary: true,
          tags: true
        }
      });

      const {
        object: { documents }
      } = await generateObject({
        model: openrouterProvider('google/gemini-2.5-pro-preview'),
        prompt: `You are a document search assistant. Analyze the user's question and the available documents to identify which documents are most relevant to answering their query.

        User Question: "${userSearchQuery}"

        Available Documents:
        ${dbDocuments.map((document) => `${document.id} (${document.name}): ${document.summary}`).join('\n')}

        Your task is to identify which documents from the list above are most relevant to answering the user's question. Consider:
        - Direct relevance to the question topic
        - Whether the document content would help answer the user's query
        - The specificity and usefulness of the information

        Return only the documents that are genuinely helpful for answering the user's question. If no documents are relevant, return an empty array.

        Note: In the next step, we will gather the unique contents of each document and research the relevant data in it.
        `,
        schema: z.object({
          documents: z.array(
            z.object({
              id: z.string(),
              name: z.string(),
              reason: z.string()
            })
          )
        })
      });

      const relevantInformationObjects: {
        id: string;
        name: string;
        relevantInformation: string;
        reason: string;
      }[] = documents.map((d) => ({
        id: d.id,
        name: d.name,
        relevantInformation: '',
        reason: d.reason
      }));

      messageStreamWriter.write({
        type: 'data-document-search',
        id,
        data: {
          status: 'documents_found',
          content: `Found ${documents.length} relevant knowledge base documents`
        }
      });

      const documentsInBatches = splitArrayBatches(
        relevantInformationObjects,
        3
      );

      for (const batch of documentsInBatches) {
        await Promise.all(
          batch.map(async (relevantInformationObject) => {
            const dbDocument = await db.query.documents.findFirst({
              where: {
                id: relevantInformationObject.id
              }
            });

            if (!dbDocument) {
              return;
            }

            messageStreamWriter.write({
              type: 'data-document-search',
              id,
              data: {
                status: 'researching_document',
                content: `Researching document ${dbDocument.name}`
              }
            });

            const { text } = await generateText({
              model: openrouterProvider('google/gemini-2.5-pro-preview'),
              messages: [
                {
                  role: 'system',
                  content: `You are an expert information extractor. Given a user query and a search result, extract all pieces of information that are relevant to answering the user's query. Return only the relevant information from the document as plain text without commentary. If you don't find any relevant information, return an empty string.`
                },
                {
                  role: 'user',
                  content: `User query: ${userSearchQuery}\nSearch result name: ${dbDocument.name}\nSearch result: ${dbDocument.content}`
                }
              ]
            });

            console.log(text);

            relevantInformationObject.relevantInformation = text;

            messageStreamWriter.write({
              type: 'data-document-search',
              id,
              data: {
                status: 'document_research_complete',
                content: text
              }
            });
          })
        );
      }

      messageStreamWriter.write({
        type: 'data-document-search',
        id,
        data: {
          status: 'document_research_complete',
          content: relevantInformationObjects
            .map((d) => d.relevantInformation)
            .join('\n')
        }
      });

      console.log(relevantInformationObjects);

      return relevantInformationObjects;
    }
  });
};

export default getToolSearchKnowledgeBase;
