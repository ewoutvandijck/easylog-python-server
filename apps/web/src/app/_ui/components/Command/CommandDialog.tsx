import { type DialogProps } from '@radix-ui/react-dialog';
import { Command } from 'cmdk';
import { VariantProps, tv } from 'tailwind-variants';

import Dialog from '../Dialog/Dialog';
import DialogContent from '../Dialog/DialogContent';

export const commandDialogStyles = tv({
  slots: {
    content: 'overflow-hidden p-0',
    command:
      '[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-text-muted [&_[cmdk-group]:not([hidden])_~[cmdk-group]]:pt-0 [&_[cmdk-group]]:px-2 [&_[cmdk-input-wrapper]_svg]:size-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:size-5'
  }
});

const { content, command } = commandDialogStyles();

export interface CommandDialogProps
  extends VariantProps<typeof commandDialogStyles>,
    DialogProps {}

const CommandDialog = ({ children, ...props }: CommandDialogProps) => {
  return (
    <Dialog {...props}>
      <DialogContent className={content()}>
        <Command className={command()}>{children}</Command>
      </DialogContent>
    </Dialog>
  );
};

export default CommandDialog;
