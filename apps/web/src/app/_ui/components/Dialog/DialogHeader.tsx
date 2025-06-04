'use client';

import * as DialogPrimitive from '@radix-ui/react-dialog';
import { IconX } from '@tabler/icons-react';
import { VariantProps, tv } from 'tailwind-variants';

import Button from '../Button/Button';
import ButtonContent from '../Button/ButtonContent';
import Icon from '../Icon/Icon';

export const dialogHeaderStyles = tv({
  slots: {
    wrapper:
      'border-border-muted flex h-12 shrink-0 items-center justify-between border-b px-4',
    content: 'flex grow items-center justify-between truncate',
    close: 'shrink-0'
  }
});

export interface DialogHeaderProps
  extends VariantProps<typeof dialogHeaderStyles> {
  className?: string;
}

const { wrapper, content, close } = dialogHeaderStyles();

const DialogHeader = ({
  className,
  children,
  ...props
}: React.PropsWithChildren<DialogHeaderProps>) => (
  <header className={wrapper({ className, ...props })}>
    <div className={content()}>{children}</div>
    <Button
      size="sm"
      asChild
      variant="ghost"
      shape="circle"
      className={close()}
    >
      <DialogPrimitive.Close>
        <ButtonContent>
          <Icon icon={IconX} colorRole="muted" />
          <span className="sr-only">Close</span>
        </ButtonContent>
      </DialogPrimitive.Close>
    </Button>
  </header>
);

export default DialogHeader;
