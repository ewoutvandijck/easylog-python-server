'use client';

import { usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import useIsMobile from '../../hooks/useIsMobile';
import Sheet from '../Sheet/Sheet';
import SheetContent from '../Sheet/SheetContent';
import SheetTitle from '../Sheet/SheetTitle';
import useSidebarContext from './hooks/useSidebarContext';

export const sidebarMobileStyles = tv({
  slots: {
    sheetContent:
      'flex flex-col overflow-hidden p-2 transition-all duration-300 ease-in-out'
  }
});

export interface SidebarMobileProps
  extends VariantProps<typeof sidebarMobileStyles> {
  className?: string;
}

const { sheetContent: sheetContentStyles } = sidebarMobileStyles();

const SidebarMobile = ({
  children,
  className
}: React.PropsWithChildren<SidebarMobileProps>) => {
  const isMobile = useIsMobile();
  const { isCollapsed, setIsCollapsed } = useSidebarContext();

  const pathname = usePathname();

  useEffect(() => {
    if (isMobile) {
      setIsCollapsed(false);
    }
  }, [isMobile, pathname, setIsCollapsed]);

  return (
    <Sheet open={isMobile && isCollapsed} onOpenChange={setIsCollapsed}>
      <SheetContent className={sheetContentStyles({ className })}>
        <SheetTitle className="sr-only">Sidebar</SheetTitle>
        <div className="relative grow">{children}</div>
      </SheetContent>
    </Sheet>
  );
};

export default SidebarMobile;
