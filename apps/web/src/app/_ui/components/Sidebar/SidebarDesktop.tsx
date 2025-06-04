'use client';

import { Resizable } from 're-resizable';
import { useEffect, useRef, useState } from 'react';
import { VariantProps, tv } from 'tailwind-variants';

import useSidebarContext from './hooks/useSidebarContext';
import useIsMobile from '../../hooks/useIsMobile';

const sidebarDesktopStyles = tv({
  slots: {
    wrapper: 'relative hidden h-full',
    handleWrapper: 'group flex h-full w-2 justify-center',
    handle:
      'bg-border-primary h-full w-1 rounded-full opacity-0 transition-opacity duration-200 group-hover:opacity-75'
  },
  variants: {
    isCollapsed: {
      false: {
        wrapper: 'md:block'
      }
    },
    isResizing: {
      true: {
        handle: 'opacity-100'
      }
    }
  }
});

const {
  wrapper: wrapperStyles,
  handleWrapper: handleWrapperStyles,
  handle: handleStyles
} = sidebarDesktopStyles();

const SNAP_GAP = 25;
const DEFAULT_WIDTH = 250;
const MIN_WIDTH = 150;
const MAX_WIDTH = 500;

export interface SidebarDesktopProps
  extends VariantProps<typeof sidebarDesktopStyles> {
  className?: string;
}

const SidebarDesktop = ({
  children,
  className
}: React.PropsWithChildren<SidebarDesktopProps>) => {
  const isMobile = useIsMobile();

  const { isCollapsed, setIsCollapsed, width, setWidth } = useSidebarContext();

  const [isResizing, setIsResizing] = useState(false);

  const resizeRef = useRef<Resizable>(null);

  useEffect(() => {
    if (!isCollapsed) {
      setWidth(width);
      resizeRef.current?.updateSize({ width });
    }
  }, [isCollapsed, setWidth, width]);

  return (
    <>
      <Resizable
        ref={resizeRef}
        as="aside"
        defaultSize={{ width }}
        minWidth={0}
        maxWidth={MAX_WIDTH}
        size={{ width }}
        enable={{
          top: false,
          right: true,
          bottom: false,
          left: false,
          topRight: false,
          bottomRight: false,
          bottomLeft: false,
          topLeft: false
        }}
        snap={{ x: [0, MIN_WIDTH, DEFAULT_WIDTH, MAX_WIDTH] }}
        snapGap={SNAP_GAP}
        className={wrapperStyles({
          className,
          isCollapsed: isCollapsed || isMobile
        })}
        onResize={(e, direction, ref, d) => {
          if (width + d.width < MIN_WIDTH) {
            setIsCollapsed(true);
          }
        }}
        onResizeStart={() => setIsResizing(true)}
        onResizeStop={(e, direction, ref, d) => {
          if (width + d.width >= MIN_WIDTH) {
            setWidth(width + d.width);
          }
          setIsResizing(false);
        }}
        handleComponent={{
          right: (
            <div className={handleWrapperStyles({ isResizing })}>
              <div className={handleStyles({ isResizing })} />
            </div>
          )
        }}
      >
        {children}
      </Resizable>
    </>
  );
};

export default SidebarDesktop;
