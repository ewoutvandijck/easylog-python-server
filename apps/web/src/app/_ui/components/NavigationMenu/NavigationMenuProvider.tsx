'use client';

import { createContext, useEffect, useState } from 'react';

export interface NavigationMenuContextType {
  hash: string | null;
  hoverElement: HTMLElement | null;
  selectedElement: HTMLElement | null;
  lastClickedElement: HTMLElement | null;
  setHoverElement: (target: HTMLElement | null) => void;
  setSelectedElement: (target: HTMLElement | null) => void;
  setLastClickedElement: (target: HTMLElement | null) => void;
}

export const NavigationMenuContext =
  createContext<NavigationMenuContextType | null>(null);

export interface NavigationMenuProviderProps {
  defaultHash?: string;
}

const NavigationMenuProvider = ({
  defaultHash,
  children
}: React.PropsWithChildren<NavigationMenuProviderProps>) => {
  const [hoverElement, setHoverElement] = useState<HTMLElement | null>(null);
  const [selectedElement, setSelectedElement] = useState<HTMLElement | null>(
    null
  );
  const [lastClickedElement, setLastClickedElement] =
    useState<HTMLElement | null>(null);
  const [hash, setHash] = useState<string | null>(defaultHash ?? null);

  useEffect(() => {
    const onHashChange = () => {
      setHash(window.location.hash);
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  useEffect(() => {
    setHash((window.location.hash || defaultHash) ?? null);
  }, [defaultHash]);

  return (
    <NavigationMenuContext.Provider
      value={{
        hash,
        hoverElement,
        selectedElement,
        lastClickedElement,
        setHoverElement,
        setSelectedElement,
        setLastClickedElement
      }}
    >
      {children}
    </NavigationMenuContext.Provider>
  );
};

export default NavigationMenuProvider;
