'use client';

import { tv } from 'tailwind-variants';

import PersistentPanel, {
  PersistentPanelProps
} from '../Panels/PersistentPanel';
import useSidebar from './hooks/useSidebarContext';
import useIsMobile from '../../hooks/useIsMobile';
import Sheet from '../Sheet/Sheet';
import SheetContent from '../Sheet/SheetContent';
import SheetTitle from '../Sheet/SheetTitle';

export const sidebarStyles = tv({
  slots: {
    sheetContent: 'px-2 transition-all duration-300 ease-in-out',
    persistentPanel: 'hidden pl-2 md:block md:pl-0'
  },
  variants: {
    isDragging: {
      false: {
        persistentPanel: 'transition-all duration-300 ease-in-out'
      }
    }
  },
  defaultVariants: {
    isDragging: false
  }
});

export interface SidebarProps
  extends Omit<PersistentPanelProps, 'order' | 'id'> {
  order?: number;
  id?: string;
}

const {
  sheetContent: sheetContentStyles,
  persistentPanel: persistentPanelStyles
} = sidebarStyles();

const Sidebar = ({
  children,
  order = 1,
  id = 'sidebar',
  className,
  ...props
}: SidebarProps) => {
  const { sidebarRef, isDragging, isCollapsed, setIsCollapsed } = useSidebar();

  const isMobile = useIsMobile();

  return (
    <>
      <Sheet
        open={!isCollapsed && isMobile}
        onOpenChange={(open) => {
          setIsCollapsed(!open);
        }}
      >
        <SheetContent
          className={sheetContentStyles({ className })}
          aria-description="Sidebar"
        >
          <SheetTitle className="sr-only">Sidebar</SheetTitle>
          {children}
        </SheetContent>
      </Sheet>
      <PersistentPanel
        ref={sidebarRef}
        order={order}
        id={id}
        collapsible={true}
        minSize={10}
        onCollapse={() => {
          setIsCollapsed(true);
        }}
        onExpand={() => {
          setIsCollapsed(false);
        }}
        className={persistentPanelStyles({ isDragging, className })}
        {...props}
      >
        {children}
      </PersistentPanel>
    </>
  );
};

export default Sidebar;
