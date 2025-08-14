import * as Sentry from '@sentry/nextjs';
import {
  UIMessageStreamWriter,
  generateObject,
  generateText,
  stepCountIs,
  tool
} from 'ai';
import { v4 as uuidv4 } from 'uuid';
import { z } from 'zod';

import db from '@/database/client';
import openrouterProvider from '@/lib/ai-providers/openrouter';
import splitArrayBatches from '@/utils/split-array-batches';
import tryCatch from '@/utils/try-catch';

interface ToolSearchKnowledgeBaseProps {
  agentId: string;
}

const getToolSearchKnowledgeBase = (
  { agentId }: ToolSearchKnowledgeBaseProps,
  messageStreamWriter: UIMessageStreamWriter
) => {
  return tool({
    description: 'Search the knowledge base for information',
    inputSchema: z.object({
      userSearchQuery: z.string().describe('The question the user asked')
    }),
    execute: async ({ userSearchQuery }) => {
      const id = uuidv4();

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
        },
        where: {
          agentId
        }
      });

      console.log('dbDocuments', dbDocuments);

      const {
        object: { documents }
      } = await generateObject({
        model: openrouterProvider('google/gemini-2.5-flash'),
        prompt: `You are a document search assistant. Analyze the user's question and the available documents to identify which documents are most relevant to answering their query.

        User Question: "${userSearchQuery}"

        Available Documents:
        ${dbDocuments.map((document) => `${document.id} (${document.name}): ${document.summary}`).join('\n')}

        Your task is to identify which documents from the list above are most relevant to answering the user's question. Consider:
        - Direct relevance to the question topic
        - Whether the document content would help answer the user's query
        - The specificity and usefulness of the information

        Return only the documents that are genuinely helpful for answering the user's question.

        Note: In the next step, we will gather the unique contents of each document and research the relevant data in it.

        Response in the following JSON format:
        {
          "documents": [
            {
              "id": "string",
              "name": "string",
              "reason": "string"
            }
          ]
        }
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

      console.log('documents', documents);

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
                content: `Researching ${dbDocument.name}: ${relevantInformationObject.reason}`
              }
            });

            const { text } = await generateText({
              model: openrouterProvider('google/gemini-2.5-flash'),
              tools: {
                toolExecuteSQL: tool({
                  description: 'Execute a SQL query on the Easylog database',
                  inputSchema: z.object({
                    query: z.string()
                  }),
                  execute: async (query) => {
                    console.log('Executing SQL query', query.query);

                    const [result, error] = await tryCatch(
                      db.execute(query.query)
                    );

                    if (error) {
                      Sentry.captureException(error);
                      console.error(error);
                      return `Error executing SQL query: ${error.message}`;
                    }

                    return JSON.stringify(result, null, 2);
                  }
                })
              },
              messages: [
                {
                  role: 'system',
                  content: `You are an expert information extractor and data analyst. Your task is to:

1. Analyze the document structure using the provided analysis object
2. Query the document_data table to extract relevant information based on the user's query
3. Return only the relevant information as plain text without commentary

The analysis object contains metadata about each column in the document:
- columnName: The name of the column
- columnType: The data type (string, number, date, boolean)
- sampleValues: Example values from the column
- uniqueValues: Number of unique values
- emptyValues: Number of empty values
- min/max: For numeric and date columns

You must use the toolExecuteSQL tool and query the document_data table to extract the actual relevant data. Based on the sample values you might think the data doesn't exist, but you must verify it.

IMPORTANT QUERY RULES:
- ALWAYS prioritize aggregate functions (COUNT, SUM, AVG, MIN, MAX) for overview and insights
- Only use LIMIT 25 for detailed row-by-row queries when user explicitly requests examples or detailed breakdowns
- Start with summary statistics and trends, then provide specific examples only if needed
- You can break up your analysis into multiple steps/queries
- The document_data table structure:
  - id: UUID (primary key)
  - document_id: UUID (foreign key to documents table)
  - part_name: TEXT (document section/part)
  - row_id: INTEGER (row number within document)
  - row_data: JSONB (contains all row data as JSON objects)
  - created_at: TIMESTAMP
  - updated_at: TIMESTAMP

The row_data column contains JSON objects where each key is a column name and the value is the corresponding data. For example:
{
  "Column1": "value1",
  "Column2": 123,
  "Column3": "2024-01-01",
  "Column4": true
}`
                },
                {
                  role: 'user',
                  content: `User query: ${userSearchQuery}

Document name: ${dbDocument.name}
Document ID: ${dbDocument.id}

Document structure analysis:
${JSON.stringify(dbDocument.analysis, null, 2)}

Based on this analysis, determine which columns might contain relevant information for the user's query. Then use the toolExecuteSQL tool to query the document_data table with the document ID to extract the actual relevant data.

QUERY STRATEGY:
1. ALWAYS prioritize aggregate functions (COUNT, SUM, AVG, MIN, MAX) for overview information
2. Only use detailed row-by-row queries (LIMIT 25) if the user explicitly asks for specific examples or detailed breakdowns
3. Start with summary statistics and trends rather than individual records
4. Use aggregate queries to understand data distribution and patterns
5. Focus on columns that seem most relevant to the user's question
6. Provide high-level insights first, then drill down only if needed

Example queries you might use (prioritize aggregates):
- **Aggregate overview**: "SELECT COUNT(*) as total_rows FROM document_data WHERE document_id = '${dbDocument.id}'"
- **Column distribution**: "SELECT row_data->>'ColumnName' as column_value, COUNT(*) FROM document_data WHERE document_id = '${dbDocument.id}' AND row_data->>'ColumnName' IS NOT NULL GROUP BY row_data->>'ColumnName' ORDER BY COUNT(*) DESC LIMIT 10"
- **Numeric analysis**: "SELECT AVG((row_data->>'NumericColumn')::numeric) as average, MIN((row_data->>'NumericColumn')::numeric) as minimum, MAX((row_data->>'NumericColumn')::numeric) as maximum FROM document_data WHERE document_id = '${dbDocument.id}' AND row_data->>'NumericColumn' IS NOT NULL"
- **Summary statistics**: "SELECT COUNT(DISTINCT row_data->>'CategoryColumn') as unique_categories, COUNT(*) as total_records FROM document_data WHERE document_id = '${dbDocument.id}'"

Only use detailed queries if user explicitly asks for examples:
- **Detailed examples** (only when requested): "SELECT part_name, row_data FROM document_data WHERE document_id = '${dbDocument.id}' LIMIT 25"
- **Specific column examples** (only when requested): "SELECT part_name, row_data->>'ColumnName' as column_value FROM document_data WHERE document_id = '${dbDocument.id}' AND row_data->>'ColumnName' IS NOT NULL LIMIT 25"

Return only the relevant information as plain text without commentary. If you don't find any relevant information, return an empty string.`
                }
              ],
              stopWhen: stepCountIs(10)
            });

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
            .join('\n-')
        }
      });

      return relevantInformationObjects;
    }
  });
};

export default getToolSearchKnowledgeBase;
