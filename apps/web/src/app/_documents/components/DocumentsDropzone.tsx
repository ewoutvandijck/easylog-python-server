'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { upload } from '@vercel/blob/client';
import { toast } from 'sonner';

import UploadDropzone from '@/app/_ui/components/UploadDropzone/UploadDropzone';
import useTRPC from '@/lib/trpc/browser';

const DocumentsDropzone = ({ children }: React.PropsWithChildren) => {
  const queryClient = useQueryClient();
  const api = useTRPC();

  const { mutateAsync: uploadFiles } = useMutation({
    mutationFn: async (files: File[]) => {
      return await Promise.all(
        files.map(async (file) => {
          const uploadResult = await upload(file.name, file, {
            access: 'public',
            handleUploadUrl: `/api/documents/upload`
          });

          return uploadResult;
        })
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: api.documents.getMany.queryKey({})
      });

      toast.success('Files uploaded');
    }
  });

  return (
    <UploadDropzone
      onDropRejected={(fileRejections) => {
        fileRejections.forEach((fileRejection) => {
          toast.error(
            fileRejection.errors.map((error) => error.message).join(', ')
          );
        });
      }}
      maxFiles={50}
      maxSize={50000000} // 50mb
      accept={{
        'application/pdf': ['.pdf']
      }}
      onDrop={async (acceptedFiles) => {
        if (acceptedFiles.length === 0) {
          return;
        }

        await uploadFiles(acceptedFiles);
      }}
    >
      {children}
    </UploadDropzone>
  );
};

export default DocumentsDropzone;
