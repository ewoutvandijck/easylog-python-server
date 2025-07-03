import * as Sentry from '@sentry/nextjs';
import { type HandleUploadBody, handleUpload } from '@vercel/blob/client';
import { eq } from 'drizzle-orm';
import { NextResponse } from 'next/server';
import { z } from 'zod';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import db from '@/database/client';
import { documents } from '@/database/schema';

export async function POST(request: Request) {
  const body = (await request.json()) as HandleUploadBody;

  const user = await getCurrentUser(request.headers);

  if (!user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const jsonResponse = await handleUpload({
      token: process.env.BLOB_READ_WRITE_TOKEN,
      body,
      request,
      onBeforeGenerateToken: async (
        pathname
        /* clientPayload */
      ) => {
        const [document] = await db
          .insert(documents)
          .values({
            path: pathname,
            type: 'pdf',
            status: 'pending'
          })
          .returning();

        return {
          allowedContentTypes: ['application/pdf'],
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
            status: 'processing',
            type: blob.contentType === 'application/pdf' ? 'pdf' : 'unknown'
          })
          .where(eq(documents.id, documentId));
      }
    });

    return NextResponse.json(jsonResponse);
  } catch (error) {
    Sentry.captureException(error);
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 400 }
    );
  }
}
