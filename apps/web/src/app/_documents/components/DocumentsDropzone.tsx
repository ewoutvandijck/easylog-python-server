'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { upload } from '@vercel/blob/client';
import { DropzoneOptions } from 'react-dropzone';
import { toast } from 'sonner';
import { v4 as uuidv4 } from 'uuid';

import UploadDropzone from '@/app/_ui/components/UploadDropzone/UploadDropzone';
import useTRPC from '@/lib/trpc/browser';

interface DocumentsDropzoneProps extends DropzoneOptions {
  onUploadSuccess?: () => void;
}

const DocumentsDropzone = ({
  children,
  onUploadSuccess,
  ...props
}: React.PropsWithChildren<DocumentsDropzoneProps>) => {
  const queryClient = useQueryClient();
  const api = useTRPC();

  const { mutateAsync: uploadFiles } = useMutation({
    mutationFn: async (files: File[]) => {
      return await Promise.all(
        files.map(async (file) => {
          const uploadResult = await upload(`${uuidv4()}/${file.name}`, file, {
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

      onUploadSuccess?.();
    }
  });

  return (
    <UploadDropzone
      {...props}
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
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': [
          '.xlsx'
        ]
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
