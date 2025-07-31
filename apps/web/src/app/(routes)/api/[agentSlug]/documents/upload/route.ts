import * as Sentry from '@sentry/nextjs';
import { type HandleUploadBody, handleUpload } from '@vercel/blob/client';
import { eq } from 'drizzle-orm';
import { NextResponse } from 'next/server';
import { z } from 'zod';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import db from '@/database/client';
import { documents } from '@/database/schema';
import { ingestDocumentJob } from '@/jobs/ingest-document/ingest-document-job';
import isUUID from '@/utils/is-uuid';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ agentSlug: string }> }
) {
  const { agentSlug } = await params;

  const agent = await db.query.agents.findFirst({
    where: {
      [isUUID(agentSlug) ? 'id' : 'slug']: agentSlug
    }
  });

  if (!agent) {
    return NextResponse.json({ error: 'Agent not found' }, { status: 404 });
  }

  const body = (await request.json()) as HandleUploadBody;

  try {
    const jsonResponse = await handleUpload({
      token: process.env.BLOB_READ_WRITE_TOKEN,
      body,
      request,
      onBeforeGenerateToken: async (pathname) => {
        const user = await getCurrentUser(request.headers);

        if (!user) {
          throw new Error('Unauthorized');
        }

        const [document] = await db
          .insert(documents)
          .values({
            name: pathname.split('/').pop() ?? 'unknown',
            agentId: agent.id,
            type: 'unknown',
            status: 'pending'
          })
          .returning();

        return {
          allowedContentTypes: [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          ],
          addRandomSuffix: true,
          tokenPayload: JSON.stringify({
            documentId: document.id
          })
        };
      },
      onUploadCompleted: async ({ blob, tokenPayload }) => {
        const { documentId } = z
          .object({
            documentId: z.string()
          })
          .parse(JSON.parse(tokenPayload ?? '{}'));

        await db
          .update(documents)
          .set({
            path: blob.pathname
          })
          .where(eq(documents.id, documentId));

        await ingestDocumentJob.trigger({
          documentId
        });
      }
    });

    return NextResponse.json(jsonResponse);
  } catch (error) {
    console.error(error);
    Sentry.captureException(error);
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 400 }
    );
  }
}
