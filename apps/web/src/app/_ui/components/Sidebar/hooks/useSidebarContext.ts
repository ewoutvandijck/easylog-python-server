import { useContext } from 'react';

import { SidebarContext } from '../SidebarProviderInner';

const useSidebar = () => {
  const context = useContext(SidebarContext);

  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }

  return context;
};

export default useSidebar;
