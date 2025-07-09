import { VariantProps, tv } from 'tailwind-variants';

import PersistentPanel from '../Panels/PersistentPanel';

export const sidebarInsetStyles = tv({
  base: 'md:shadow-xs box-content flex h-full flex-col border-border-primary bg-background-primary md:rounded-md md:border'
});

export interface SidebarInsetProps
  extends React.PropsWithChildren,
    VariantProps<typeof sidebarInsetStyles> {
  className?: string;
}

const SidebarInset = ({ children, className }: SidebarInsetProps) => {
  return (
    <PersistentPanel
      order={2}
      id={'sidebar-main'}
      tagName="main"
      className={sidebarInsetStyles({ className })}
    >
      {children}
    </PersistentPanel>
  );
};

export default SidebarInset;
