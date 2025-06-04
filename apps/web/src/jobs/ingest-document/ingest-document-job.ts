import { HeadObjectCommand } from '@aws-sdk/client-s3';
import { AbortTaskRunError, logger, schemaTask } from '@trigger.dev/sdk';
import { generateObject } from 'ai';
import { z } from 'zod';

import db from '@/database/client';
import { documents } from '@/database/schema';
import s3Client from '@/lib/aws-s3/client';
import openrouterProvider from '@/lib/openrouter/ai-provider';
import getDocumentsCollection from '@/lib/weaviate/collections/documents';
import serverEnv from '@/server.env';

import { processPdfJob } from './converters/process-pdf-job';

export const ingestDocumentJob = schemaTask({
  id: 'ingest-document',
  schema: z.object({
    organizationId: z.string(),
    filename: z.string()
  }),
  run: async ({ organizationId, filename }) => {
    const headResponse = await s3Client.send(
      new HeadObjectCommand({
        Bucket: serverEnv.S3_PUBLIC_BUCKET_NAME,
        Key: filename
      })
    );

    const contentType = headResponse.ContentType;

    if (contentType !== 'application/pdf') {
      throw new AbortTaskRunError('Unsupported content type');
    }

    logger.info('Processing document', { filename, contentType });

    const processingResult = await processPdfJob.triggerAndWait({
      filename: filename
    });

    if (!processingResult.ok) {
      throw new AbortTaskRunError('Failed to process document');
    }

    logger.info('Processing result', { processingResult });

    const {
      object: { summary, tags }
    } = await generateObject({
      model: openrouterProvider('google/gemini-2.5-pro-preview'),
      prompt: `Act as a professional summarizer. Create a concise and summary of the <text> below, while adhering to the guidelines enclosed in <guidelines> below.

      <guidelines>
        - Ensure that the summary includes relevant details, while avoiding any unnecessary information or repetition. 
        - Rely strictly on the provided text, without including external information.
        - The length of the summary must be within 1000 characters.
        - Your summary must always be in english.
        - Generate tags for unique entities in the text (like people, companies, locations, etc.)
      </guidelines>

      <text>
        ${JSON.stringify(processingResult.output, null, 2)}
      </text>
      `,
      schema: z.object({
        summary: z.string(),
        tags: z.array(z.string())
      })
    });

    logger.info('Summary', { summary, tags });

    const weaviateId = await (
      await getDocumentsCollection()
    ).data.insert({
      filename,
      organizationId,
      summary,
      tags
    });

    const [document] = await db
      .insert(documents)
      .values({
        organizationId,
        vectorDocumentId: weaviateId,
        path: filename,
        type: 'pdf',
        summary,
        tags,
        content: {
          pages: processingResult.output.map((page) => ({
            pageNumber: page.pageNumber,
            markdown: page.markdown
          }))
        }
      })
      .returning();

    logger.info('Document inserted', { document });
  }
});
