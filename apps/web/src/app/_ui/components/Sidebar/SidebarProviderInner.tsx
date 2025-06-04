'use client';

import { usePathname } from 'next/navigation';
import { createContext, useEffect, useRef, useState } from 'react';
import { ImperativePanelHandle } from 'react-resizable-panels';

import useIsMobile from '../../hooks/useIsMobile';
import useKeyboardShortcut from '../../hooks/useKeyboardShortcut';
import usePersistentPanelsContext from '../Panels/usePersistentPanelsContext';

interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (isCollapsed: boolean) => void;

  sidebarRef: React.RefObject<ImperativePanelHandle | null>;

  isDragging: boolean;
  setIsDragging: (isDragging: boolean) => void;
}

export const SidebarContext = createContext<SidebarContextType | undefined>(
  undefined
);

export interface SidebarProviderInnerProps extends React.PropsWithChildren {}

const SidebarProviderInner = ({ children }: SidebarProviderInnerProps) => {
  const { layout } = usePersistentPanelsContext();
  const isMobile = useIsMobile();
  const pathname = usePathname();

  const [isDragging, setIsDragging] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(layout[0] === 0);
  const sidebarRef = useRef<ImperativePanelHandle>(null);

  useKeyboardShortcut(['cmd', 'b'], () => {
    if (isCollapsed) {
      sidebarRef.current?.expand();
    } else {
      sidebarRef.current?.collapse();
    }
  });

  useEffect(() => {
    if (isMobile) return;

    if (isCollapsed) {
      sidebarRef.current?.collapse();
    } else {
      sidebarRef.current?.expand();
    }
  }, [isCollapsed, isMobile]);

  useEffect(() => {
    if (!isMobile) return;
    setIsCollapsed(true);
  }, [pathname, isMobile, setIsCollapsed]);

  const value = {
    isCollapsed,
    setIsCollapsed,
    isDragging,
    setIsDragging,
    sidebarRef
  };

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
};

export default SidebarProviderInner;
