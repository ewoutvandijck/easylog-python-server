'use client';

import { tv } from 'tailwind-variants';

import ResizableHandle, {
  ResizableHandleProps
} from '../Resizable/ResizableHandle';
import useSidebar from './hooks/useSidebarContext';

export const sidebarHandleStyles = tv({
  base: 'my-2 hidden h-[calc(100dvh-2rem)] w-0.5 rounded-full bg-background-muted transition-all md:block',
  variants: {
    isCollapsed: {
      true: 'w-0! overflow-hidden opacity-0',
      false: 'mx-1'
    }
  }
});

export interface SidebarHandleProps extends ResizableHandleProps {}

const SidebarHandle = ({
  children,
  className,
  ...props
}: SidebarHandleProps) => {
  const { isCollapsed, setIsDragging } = useSidebar();

  return (
    <ResizableHandle
      className={sidebarHandleStyles({
        isCollapsed: isCollapsed,
        className
      })}
      onDragging={setIsDragging}
      {...props}
    >
      {children}
    </ResizableHandle>
  );
};

export default SidebarHandle;
