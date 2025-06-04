import * as CollapsiblePrimitive from '@radix-ui/react-collapsible';
import { VariantProps, tv } from 'tailwind-variants';

export const collapsibleContentStyles = tv({
  base: 'outline-hidden text-text-primary data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2'
});

export interface CollapsibleContentProps
  extends CollapsiblePrimitive.CollapsibleContentProps,
    VariantProps<typeof collapsibleContentStyles> {}

const CollapsibleContent = ({
  className,
  children,
  ...props
}: CollapsibleContentProps) => {
  return (
    <CollapsiblePrimitive.CollapsibleContent
      className={collapsibleContentStyles({ className })}
      {...props}
    >
      {children}
    </CollapsiblePrimitive.CollapsibleContent>
  );
};

export default CollapsibleContent;
