'use client';

import { useState } from 'react';

import Dialog from '@/app/_ui/components/Dialog/Dialog';
import DialogBody from '@/app/_ui/components/Dialog/DialogBody';
import DialogContent from '@/app/_ui/components/Dialog/DialogContent';
import DialogHeader from '@/app/_ui/components/Dialog/DialogHeader';
import DialogTitle from '@/app/_ui/components/Dialog/DialogTitle';
import Typography from '@/app/_ui/components/Typography/Typography';

import DocumentsDropzone from './DocumentsDropzone';

export interface DocumentsUploadDialogProps {
  agentSlug: string;
}

const DocumentsUploadDialog = ({
  children,
  agentSlug
}: React.PropsWithChildren<DocumentsUploadDialogProps>) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      {children}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
        </DialogHeader>
        <DocumentsDropzone
          onUploadSuccess={() => setIsOpen(false)}
          agentSlug={agentSlug}
        >
          <DialogBody>
            <div className="border-border-primary hover:bg-surface-primary-hover active:bg-surface-primary-active flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed p-4 transition-all">
              <Typography>
                Klik of sleep hier documenten die je wilt toevoegen aan de
                kennisbank.
              </Typography>
            </div>
          </DialogBody>
        </DocumentsDropzone>
      </DialogContent>
    </Dialog>
  );
};

export default DocumentsUploadDialog;
