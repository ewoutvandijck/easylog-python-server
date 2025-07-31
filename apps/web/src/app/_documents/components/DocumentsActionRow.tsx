import { IconUpload } from '@tabler/icons-react';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import DialogTrigger from '@/app/_ui/components/Dialog/DialogTrigger';

import DocumentsUploadDialog from './DocumentsUploadDialog';

interface DocumentsActionRowProps {
  agentSlug: string;
}

const DocumentsActionRow = ({ agentSlug }: DocumentsActionRowProps) => {
  return (
    <div className="flex items-center justify-between">
      <DocumentsUploadDialog agentSlug={agentSlug}>
        <DialogTrigger asChild>
          <Button>
            <ButtonContent iconLeft={IconUpload}>
              Documenten uploaden
            </ButtonContent>
          </Button>
        </DialogTrigger>
      </DocumentsUploadDialog>
    </div>
  );
};

export default DocumentsActionRow;
