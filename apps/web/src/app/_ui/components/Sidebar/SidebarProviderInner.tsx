'use client';

import { useAtom } from 'jotai';
import { createContext, useMemo } from 'react';
import { z } from 'zod';

import createCookieAtom from '../../utils/createCookieAtom';

interface SidebarContextType {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  width: number;
  setWidth: (width: number) => void;
}

export const SidebarContext = createContext<SidebarContextType | undefined>(
  undefined
);

interface SidebarProviderInnerProps {
  cookieName: string;
  initialWidth: number;
  initialIsCollapsed: boolean;
}

const SidebarProviderInner = ({
  children,
  cookieName,
  initialWidth,
  initialIsCollapsed
}: React.PropsWithChildren<SidebarProviderInnerProps>) => {
  const widthAtom = useMemo(
    () =>
      createCookieAtom(
        `${cookieName}.width`,
        z.string().transform((val) => Number(val)),
        initialWidth
      ),
    [cookieName, initialWidth]
  );

  const isCollapsedAtom = useMemo(
    () =>
      createCookieAtom(
        `${cookieName}.is-collapsed`,
        z.string().transform((val) => val === 'true'),
        initialIsCollapsed
      ),
    [cookieName, initialIsCollapsed]
  );

  const [width, setWidth] = useAtom(widthAtom);
  const [isCollapsed, setIsCollapsed] = useAtom(isCollapsedAtom);

  return (
    <SidebarContext.Provider
      value={{
        isCollapsed,
        setIsCollapsed,
        width,
        setWidth
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
};

export default SidebarProviderInner;
