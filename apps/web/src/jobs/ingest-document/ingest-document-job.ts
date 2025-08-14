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

import { processPdfJob } from './converters/process-pdf-job';
import { processXlsxJob } from './converters/process-xlsx-job';
import analyzeColumn from './utils/analyzeColumn';

export const ingestDocumentJob = schemaTask({
  id: 'ingest-document',
  schema: z.object({
    documentId: z.string()
  }),
  machine: 'large-1x',
  run: async ({ documentId }) => {
    const dbDocument = await db.query.documents.findFirst({
      where: {
        id: documentId
      },
      with: {
        agent: true
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

    const processingResult =
      contentType === 'application/pdf'
        ? await processPdfJob.triggerAndWait({
            downloadUrl: headResponse.downloadUrl,
            basePath: dbDocument.path
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
      model: openrouterProvider(dbDocument.agent.config.model),
      prompt: `You are a professional data analyst and summarizer. Your task is to analyze the provided data structure and create a comprehensive summary with relevant tags.

## TASK
Analyze the data structure below and provide:
1. A concise summary (max 1000 characters) describing the data content, structure, and key insights
2. An array of relevant tags identifying entities, categories, and themes

## DATA STRUCTURE
The data represents either:
- A spreadsheet with multiple parts, each containing columns with different data types (string, number, date, boolean)
- A PDF document with multiple pages, each containing markdown text and images

## REQUIREMENTS
- Summary must be in English and under 1000 characters
- Summary should describe the overall content, structure, and key patterns
- For spreadsheets: describe data types, columns, and key insights
- For PDFs: describe the document type, content themes, and key information
- Tags should identify: companies, people, locations, dates, categories, document types, and themes
- Tags must be simple strings (no special characters or spaces)
- Always return exactly 2 fields: "summary" and "tags"

## EXAMPLE OUTPUT FORMATS

For Spreadsheets:
{
  "summary": "This document contains sales data from Q1 2024 with customer information, product details, and transaction amounts. The data includes 3 sheets with customer names, product categories, and financial figures.",
  "tags": ["sales", "customers", "products", "financial", "Q1-2024", "transactions"]
}

For PDFs:
{
  "summary": "This PDF contains a technical report with 5 pages covering system architecture, performance metrics, and implementation guidelines. Includes diagrams and detailed specifications.",
  "tags": ["technical-report", "architecture", "performance", "specifications", "diagrams"]
}

## DATA TO ANALYZE
${JSON.stringify(analysis, null, 2)}

Remember: Return ONLY the JSON object with "summary" and "tags" fields. Do not include any other text or formatting.`,
      schema: z.object({
        summary: z.string().max(1000),
        tags: z.array(z.string().min(1)).min(1)
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
      return part.data.map((record, rowIndex) => ({
        documentId,
        partName: part.name,
        rowId: rowIndex,
        rowData: record
      }));
    });

    const insertBatches = splitArrayBatches(insertData, 50);

    await db.transaction(async (tx) => {
      for (const [index, batch] of insertBatches.entries()) {
        try {
          logger.info('Inserting document data batch', {
            batchNumber: index + 1,
            batchLength: batch.length
          });

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
