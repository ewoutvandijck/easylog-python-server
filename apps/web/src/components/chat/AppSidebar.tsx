'use client';

import { Sidebar, SidebarHeader, SidebarRail } from '../ui/sidebar';
import ConnectionSwitcher from './ConnectionSwitcher';

const AppSidebar = () => {
  return (
    <Sidebar>
      <SidebarHeader>
        <ConnectionSwitcher />
      </SidebarHeader>
      <SidebarRail />
    </Sidebar>
  );
};

export default AppSidebar;
