import path from 'path';

import { logger, schemaTask } from '@trigger.dev/sdk';
import { put } from '@vercel/blob';
import { z } from 'zod';

import mistralClient from '@/lib/mistral/client';
import serverConfig from '@/server.config';

export const processPdfJob = schemaTask({
  id: 'process-pdf',
  schema: z.object({
    downloadUrl: z.string(),
    basePath: z.string()
  }),
  run: async ({ downloadUrl, basePath }) => {
    logger.info('Document URL', { downloadUrl });

    const ocrResult = await mistralClient.ocr.process({
      model: 'mistral-ocr-latest',
      document: {
        type: 'document_url',
        documentUrl: downloadUrl
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

            const blob = await put(imagePath, Buffer.from(base64, 'base64'), {
              token: serverConfig.vercelBlobReadWriteToken,
              access: 'public',
              addRandomSuffix: true,
              contentType
            });

            return {
              id: image.id,
              path: imagePath,
              contentType,
              publicUrl: blob.url
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
