import { CollapsibleProps } from '@radix-ui/react-collapsible';
import { VariantProps, tv } from 'tailwind-variants';

import Collapsible from '../Collapsible/Collapsible';

export const sideCollapsibleStyles = tv({
  base: ''
});

export interface SidebarCollapsibleProps
  extends CollapsibleProps,
    VariantProps<typeof sideCollapsibleStyles> {}

const SidebarCollapsible = ({
  className,
  children,
  ...props
}: SidebarCollapsibleProps) => {
  return (
    <Collapsible className={sideCollapsibleStyles({ className })} {...props}>
      {children}
    </Collapsible>
  );
};

export default SidebarCollapsible;
