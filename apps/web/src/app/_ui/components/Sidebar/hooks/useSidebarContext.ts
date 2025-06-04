import { useContext } from 'react';

import { SidebarContext } from '../SidebarProviderInner';

const useSidebarContext = () => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebarContext must be used within a SidebarProvider');
  }
  return context;
};

export default useSidebarContext;
