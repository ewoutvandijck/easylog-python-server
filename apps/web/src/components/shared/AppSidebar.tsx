'use client';

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator
} from '../ui/sidebar';
import ConnectionSwitcher from '../chat/ConnectionSwitcher';
import AppSidebarConfigurationMenu from './AppSidebarConfigurationMenu';
import AppSidebarThreadsMenu from './AppSidebarThreadsMenu';
import AppSidebarNew from './AppSidebarNew';

const AppSidebar = () => {
  return (
    <Sidebar>
      <SidebarHeader>
        <ConnectionSwitcher />
        <AppSidebarNew />
        <AppSidebarThreadsMenu />
      </SidebarHeader>
      <SidebarContent />
      <SidebarSeparator />
      <SidebarFooter>
        <AppSidebarConfigurationMenu />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
};

export default AppSidebar;
