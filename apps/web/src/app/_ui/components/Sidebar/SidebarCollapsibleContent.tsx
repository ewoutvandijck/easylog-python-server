import { VariantProps, tv } from 'tailwind-variants';

import CollapsibleContent, {
  CollapsibleContentProps
} from '../Collapsible/CollapsibleContent';

export const sidebarCollapsibleContentStyles = tv({
  base: 'my-0.5 flex flex-col gap-0.5'
});

export interface SidebarCollapsibleContentProps
  extends CollapsibleContentProps,
    VariantProps<typeof sidebarCollapsibleContentStyles> {}

const SidebarCollapsibleContent = ({
  className,
  children,
  ...props
}: SidebarCollapsibleContentProps) => {
  return (
    <CollapsibleContent
      className={sidebarCollapsibleContentStyles({ className })}
      {...props}
    >
      {children}
    </CollapsibleContent>
  );
};

export default SidebarCollapsibleContent;
