import { IconUpload } from '@tabler/icons-react';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import DialogTrigger from '@/app/_ui/components/Dialog/DialogTrigger';

import DocumentsUploadDialog from './DocumentsUploadDialog';

const DocumentsActionRow = () => {
  return (
    <div className="flex items-center justify-between">
      <DocumentsUploadDialog>
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
