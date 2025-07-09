'use client';

import { IconUpload } from '@tabler/icons-react';
import { DropzoneOptions, useDropzone } from 'react-dropzone';
import { tv } from 'tailwind-variants';

export const uploadDropzoneStyles = tv({
  slots: {
    root: 'relative size-full',
    overlay: 'transition-opacity duration-300',
    dropIndicator:
      'absolute left-1/2 top-1/2 z-20 -translate-x-1/2 -translate-y-1/2',
    dropIndicatorContent:
      'border-border-focus bg-surface-primary flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-8 shadow-lg',
    dropIndicatorText: 'text-text-primary text-xl font-medium',
    dropIndicatorIcon: 'text-text-primary size-12'
  },
  variants: {
    isDragActive: {
      true: {
        overlay: 'opacity-30'
      },
      false: {
        overlay: 'opacity-100'
      }
    }
  }
});

interface UploadDropzoneProps extends DropzoneOptions {}

const {
  root,
  overlay,
  dropIndicator,
  dropIndicatorContent,
  dropIndicatorText,
  dropIndicatorIcon
} = uploadDropzoneStyles();

const UploadDropzone = ({
  children,
  ...props
}: React.PropsWithChildren<UploadDropzoneProps>) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    ...props
  });

  return (
    <div className={root()} {...getRootProps()}>
      <input {...getInputProps()} />

      {/* Children with fade effect when files are dragged over */}
      <div className={overlay({ isDragActive })}>{children}</div>

      {/* Overlay that appears when files are dragged over */}
      {isDragActive && (
        <>
          {/* Semi-transparent overlay that covers the entire area */}
          <div className={dropIndicator()} />

          {/* Centered drop indicator that's fixed in the viewport */}
          <div className={dropIndicatorContent()}>
            <IconUpload className={dropIndicatorIcon()} />
            <span className={dropIndicatorText()}>
              Drop files here to upload
            </span>
          </div>
        </>
      )}
    </div>
  );
};

export default UploadDropzone;
