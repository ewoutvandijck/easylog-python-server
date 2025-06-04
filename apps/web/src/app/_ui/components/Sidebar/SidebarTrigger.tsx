'use client';

import { Slot } from '@radix-ui/react-slot';
import { ButtonHTMLAttributes } from 'react';

import useSidebar from './hooks/useSidebarContext';

export interface SidebarTriggerProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const SidebarTrigger = ({ asChild, ...props }: SidebarTriggerProps) => {
  const { isCollapsed, setIsCollapsed } = useSidebar();

  const T = asChild ? Slot : 'button';

  return (
    <T
      {...props}
      onClick={() => setIsCollapsed(!isCollapsed)}
      aria-label="Toggle sidebar"
      title="Toggle sidebar"
      tabIndex={-1}
    />
  );
};

export default SidebarTrigger;
