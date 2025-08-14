import { AbortTaskRunError, logger, schemaTask } from '@trigger.dev/sdk';
import { head } from '@vercel/blob';
import { generateObject } from 'ai';
import { eq } from 'drizzle-orm';
import { z } from 'zod';

import db from '@/database/client';
import { documentData, documents } from '@/database/schema';
import openrouterProvider from '@/lib/ai-providers/openrouter';
import serverConfig from '@/server.config';
import splitArrayBatches from '@/utils/split-array-batches';

import { processXlsxJob } from './converters/process-xlsx-job';
import analyzeColumn from './utils/analyzeColumn';

export const ingestDocumentJob = schemaTask({
  id: 'ingest-document',
  schema: z.object({
    documentId: z.string()
  }),
  run: async ({ documentId }) => {
    const dbDocument = await db.query.documents.findFirst({
      where: {
        id: documentId
      }
    });

    if (!dbDocument || !dbDocument.path) {
      throw new AbortTaskRunError('Document not found or path is missing');
    }

    const headResponse = await head(dbDocument.path, {
      token: serverConfig.vercelBlobReadWriteToken
    });

    const contentType = headResponse.contentType;

    const supportedContentTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (!supportedContentTypes.includes(contentType)) {
      throw new AbortTaskRunError(`Unsupported content type ${contentType}`);
    }

    logger.info('Processing document', {
      filename: dbDocument.name,
      downloadUrl: headResponse.downloadUrl,
      contentType
    });

    if (contentType === 'application/pdf') {
      throw new AbortTaskRunError('PDF processing not supported yet');
    }

    const processingResult =
      contentType === 'application/pdf'
        ? await processXlsxJob.triggerAndWait({
            downloadUrl: headResponse.downloadUrl
          })
        : await processXlsxJob.triggerAndWait({
            downloadUrl: headResponse.downloadUrl
          });

    if (!processingResult.ok) {
      throw new AbortTaskRunError('Failed to process document');
    }

    logger.info('Processing result', { processingResult });

    const analysis = processingResult.output.map((part) => {
      return {
        partName: part.name,
        analysis: part.columns.map((column) => {
          return analyzeColumn(part.data, column);
        })
      };
    });

    logger.info('Analysis', { analysis });

    const {
      object: { summary, tags }
    } = await generateObject({
      model: openrouterProvider('google/gemini-2.5-flash'),
      prompt: `Act as a professional summarizer. Create a concise and summary of the <text> below, while adhering to the guidelines enclosed in <guidelines> below.

      <guidelines>
        - Ensure that the summary includes relevant details, while avoiding any unnecessary information or repetition. 
        - Rely strictly on the provided text, without including external information.
        - The length of the summary must be within 1000 characters.
        - Your summary must always be in English.
        - Generate tags for unique entities in the text (like people, companies, locations, etc.)
      </guidelines>

      <filetype>
        ${contentType}
      </filetype>

      <text>
        ${JSON.stringify(analysis, null, 2)}
      </text>
      `,
      schema: z.object({
        summary: z.string(),
        tags: z.string().array()
      })
    });

    logger.info('Summary', { summary, tags });

    const [document] = await db
      .update(documents)
      .set({
        type: contentType === 'application/pdf' ? 'pdf' : 'xlsx',
        summary,
        tags,
        analysis
      })
      .where(eq(documents.id, documentId))
      .returning();

    const insertData = processingResult.output.flatMap((part) => {
      const analysisMap = new Map(
        analysis
          .find((a) => a.partName === part.name)!
          .analysis.map((a) => [a.columnName, a])
      );

      return part.data.flatMap((record, rowIndex) => {
        return part.columns.map((columnName) => {
          const value = record[columnName];
          const analysis = analysisMap.get(columnName)!;

          return {
            documentId,
            partName: part.name,
            columnName,
            columnType: analysis.columnType,
            rowId: rowIndex,
            valueString: analysis.columnType === 'string' ? value : undefined,
            valueNumber: analysis.columnType === 'number' ? value : undefined,
            valueDate: analysis.columnType === 'date' ? value : undefined,
            valueBoolean: analysis.columnType === 'boolean' ? value : undefined
          } as typeof documentData.$inferInsert;
        });
      });
    });

    const insertBatches = splitArrayBatches(insertData, 50);

    await db.transaction(async (tx) => {
      for (const batch of insertBatches) {
        try {
          await tx.insert(documentData).values(batch);
        } catch (error) {
          logger.error('Error inserting document data', { error, batch });
          throw error;
        }
      }
    });

    logger.info('Document inserted', { document });
  }
});
