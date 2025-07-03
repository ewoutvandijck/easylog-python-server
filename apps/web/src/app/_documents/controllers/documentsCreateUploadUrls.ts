import { PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { z } from 'zod';

import s3Client from '@/lib/aws-s3/client';
import { protectedProcedure } from '@/lib/trpc/procedures';
import serverConfig from '@/server.config';

const documentsCreateUploadUrls = protectedProcedure
  .input(
    z
      .object({
        fileName: z.string(),
        fileType: z.literal('application/pdf')
      })
      .array()
  )
  .mutation(async ({ input }) => {
    const uploadCommands = input.map(({ fileName, fileType }) => {
      return new PutObjectCommand({
        Bucket: serverConfig.s3PublicBucketName,
        Key: `${crypto.randomUUID()}/${fileName}`,
        ContentType: fileType
      });
    });

    const uploadUrls = await Promise.all(
      uploadCommands.map((uploadCommand) =>
        getSignedUrl(s3Client, uploadCommand, {
          expiresIn: 300 // 5 minutes
        })
      )
    );

    const uploads = input.map((_, index) => ({
      path: uploadCommands[index].input.Key!,
      uploadUrl: uploadUrls[index]
    }));

    return { uploads };
  });

export default documentsCreateUploadUrls;
