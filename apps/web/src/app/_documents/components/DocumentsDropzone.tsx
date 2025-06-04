'use client';

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'sonner';

import useOrganizationSlug from '@/app/_organizations/hooks/useOrganizationSlug';
import UploadDropzone from '@/app/_shared/components/UploadDropzone';
import useFileUploads from '@/app/_shared/hooks/useFileUploads';
import useTRPC from '@/lib/trpc/browser';

const DocumentsDropzone = ({ children }: React.PropsWithChildren) => {
  const [toastId, setToastId] = useState<string | number | undefined>(
    undefined
  );

  const organizationSlug = useOrganizationSlug();
  const api = useTRPC();

  const { mutateAsync: createUploadUrls } = useMutation(
    api.documents.createUploadUrls.mutationOptions({
      onMutate: () => {
        setToastId(toast.loading('Creating upload URLs...'));
      },
      onError: (error) => {
        toast.dismiss(toastId);
        toast.error(error.message);
      }
    })
  );

  const { mutate: uploadFiles } = useFileUploads({
    concurrencyLimit: 3,
    onUploadError: (error) => {
      toast.error(error.message);
    },
    onProgress: ({ progress, total }) => {
      toast.loading(`Uploading ${progress} of ${total} files`, {
        id: toastId
      });
    },
    onSuccess: (uploads) => {
      void batchProcess({
        organizationId: organizationSlug,
        filePaths: uploads.map((upload) => upload.path)
      });
    },
    onError: (error) => {
      toast.dismiss(toastId);
      toast.error(error.message);
    }
  });

  const { mutateAsync: batchProcess } = useMutation(
    api.documents.batchProcess.mutationOptions({
      onSuccess: () => {
        toast.dismiss(toastId);
        toast.success(`Uploaded files`);
      },
      onError: (error) => {
        toast.dismiss(toastId);
        toast.error(error.message);
      }
    })
  );

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
      onDrop={async (acceptedFiles) => {
        if (acceptedFiles.length === 0) {
          return;
        }

        const uploads = (
          await createUploadUrls(
            acceptedFiles.map((file) => ({
              fileName: file.name,
              fileType: file.type as 'application/pdf'
            }))
          )
        ).uploads;

        uploadFiles(
          acceptedFiles.map((file, index) => ({
            ...uploads[index],
            file
          }))
        );
      }}
    >
      {children}
    </UploadDropzone>
  );
};

export default DocumentsDropzone;
