import path from 'path';

import { PutObjectCommand } from '@aws-sdk/client-s3';
import { logger, schemaTask } from '@trigger.dev/sdk';
import { z } from 'zod';

import clientConfig from '@/client.config';
import s3Client from '@/lib/aws-s3/client';
import mistralClient from '@/lib/mistral/client';
import serverEnv from '@/server.env';

export const processPdfJob = schemaTask({
  id: 'process-pdf',
  schema: z.object({
    filename: z.string()
  }),
  run: async ({ filename }) => {
    const basePath = path.dirname(filename);

    logger.info('Base path', { basePath });

    const documentUrl = new URL(
      path.join(`/s3/${serverEnv.S3_PUBLIC_BUCKET_NAME}`, filename),
      clientConfig.appUrl
    );

    logger.info('Document URL', { documentUrl });

    const ocrResult = await mistralClient.ocr.process({
      model: 'mistral-ocr-latest',
      document: {
        type: 'document_url',
        documentUrl: documentUrl.toString()
      },
      includeImageBase64: true
    });

    logger.info('OCR result', { ocrResult });

    const pages = await Promise.all(
      ocrResult.pages.map(async (page) => {
        const images = await Promise.all(
          page.images.map(async (image) => {
            const imagePath = path.join(basePath, `${image.id}`);

            const imageData = image.imageBase64;

            if (!imageData) {
              logger.warn('No image base64', { imagePath });
              return {
                id: image.id,
                path: imagePath,
                contentType: 'image/jpeg',
                publicUrl:
                  'data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
              };
            }

            const contentType =
              imageData.match(/^data:(.*);base64,/)?.[1] ?? 'image/jpeg';

            const base64 = imageData.replace(`data:${contentType};base64,`, '');

            await s3Client.send(
              new PutObjectCommand({
                Bucket: serverEnv.S3_PUBLIC_BUCKET_NAME,
                Key: imagePath,
                Body: Buffer.from(base64, 'base64'),
                ContentType: contentType,
                ContentEncoding: 'base64'
              })
            );

            const publicUrl = new URL(
              path.join(`/s3/${serverEnv.S3_PUBLIC_BUCKET_NAME}`, imagePath),
              clientConfig.appUrl
            );

            return {
              id: image.id,
              path: imagePath,
              contentType,
              publicUrl: publicUrl.toString()
            };
          })
        );

        logger.info('Images', { images });

        const markdown = page.markdown.replace(
          /!\[.*?\]\((.*?)\)/g,
          (_, p1) => {
            logger.info('Markdown image', { p1 });
            const image = images.find(
              (image) => image.id === p1 || image.path === p1
            );
            return `![${image?.id ?? p1}](${image?.publicUrl ?? p1})`;
          }
        );

        return {
          pageNumber: page.index + 1,
          markdown
        };
      })
    );

    logger.info('Pages', { pages });

    return pages;
  }
});
