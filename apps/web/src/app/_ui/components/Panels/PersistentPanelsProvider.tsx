'use client';

import { setCookie } from 'cookies-next';
import { Children, createContext, useState } from 'react';

import ResizablePanelGroup, {
  ResizablePanelGroupProps
} from '../Resizable/ResizablePanelGroup';

export type PersistentPanelsContextType = {
  layout: number[];
};

export const PersistentPanelsContext =
  createContext<PersistentPanelsContextType | null>(null);

export interface PersistentPanelsProviderProps {
  cookieName?: string;
  defaultLayout?: number[];
}

const PersistentPanelsProvider = ({
  children,
  cookieName = 'panels.layout',
  defaultLayout,
  ...props
}: React.PropsWithChildren<
  PersistentPanelsProviderProps & ResizablePanelGroupProps
>) => {
  const layoutSize = defaultLayout
    ? defaultLayout.length
    : Children.count(children);

  const [layout, setLayout] = useState(
    defaultLayout && defaultLayout.length === layoutSize
      ? defaultLayout
      : Array(layoutSize)
          .fill(100 / layoutSize)
          .map((size, index) => (index % 2 === 0 ? size : 10))
  );

  return (
    <PersistentPanelsContext.Provider value={{ layout }}>
      <ResizablePanelGroup
        {...props}
        onLayout={async (layout) => {
          /**
           * Hacky way to prevent collapsing panels to 0px to cause the last
           * layout not to be saved.
           */
          if (layout.length === layout.length) {
            await setCookie(cookieName, JSON.stringify(layout));
            setLayout(layout);
          }
        }}
      >
        {children}
      </ResizablePanelGroup>
    </PersistentPanelsContext.Provider>
  );
};

export default PersistentPanelsProvider;
