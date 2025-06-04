'use client';

import { UseMutationOptions, useMutation } from '@tanstack/react-query';

import splitArrayBatches from '@/utils/split-array-batches';

export type FileUploadTask = {
  /** The file to upload. */
  file: File;

  /** The path to upload the file to. */
  path: string;

  /** The upload URL to use for the file. */
  uploadUrl: string;
};

export interface UseFileUploadProps
  extends Omit<
    UseMutationOptions<FileUploadTask[], Error, FileUploadTask[]>,
    'mutationFn'
  > {
  onProgress?: ({
    progress,
    total
  }: {
    progress: number;
    total: number;
  }) => void;
  onUploadError?: (error: Error) => void;
  concurrencyLimit?: number;
}

const useFileUploads = ({
  onProgress,
  onUploadError,
  concurrencyLimit = 3,
  ...props
}: UseFileUploadProps = {}) => {
  const mutation = useMutation({
    mutationFn: async (uploadTasks: FileUploadTask[]) => {
      let totalUploads = 0;

      const uploadPromises = uploadTasks.map((uploadTask) => async () => {
        totalUploads++;

        const response = await fetch(uploadTask.uploadUrl, {
          method: 'PUT',
          body: uploadTask.file
          // headers: {
          //   'Content-Type': uploadTask.
          // }
        });

        if (!response.ok) {
          onUploadError?.(new Error('Failed to upload file'));
          return null;
        } else {
          onProgress?.({ progress: totalUploads, total: uploadTasks.length });
        }

        return uploadTask;
      });

      const batches = splitArrayBatches(uploadPromises, concurrencyLimit);

      const results: FileUploadTask[] = [];
      for (const batch of batches) {
        results.push(
          ...((
            await Promise.allSettled(batch.map((uploadFn) => uploadFn())).then(
              (results) =>
                results.map((result) =>
                  result.status === 'fulfilled' ? result.value : null
                )
            )
          ).filter(Boolean) as FileUploadTask[])
        );
      }

      return results;
    },
    ...props
  });

  return mutation;
};

export default useFileUploads;
