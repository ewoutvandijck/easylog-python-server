'use client';

import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '../ui/sidebar';
import useThreads from '@/hooks/use-threads';
import Link from 'next/link';
import useThreadId from '@/hooks/use-thread-id';
import useIsConnectionHealthy from '@/hooks/use-is-connection-healthy';

const AppSidebarThreadsMenu = () => {
  const { data: threads } = useThreads();
  const { data: isConnected } = useIsConnectionHealthy();

  const threadId = useThreadId();

  return (
    <SidebarMenu>
      {threads?.data.map((item) => (
        <SidebarMenuItem key={item.id}>
          <SidebarMenuButton
            asChild
            isActive={threadId === item.externalId || threadId === item.id}
            disabled={!isConnected}
          >
            <Link href={`/${item.externalId ? item.externalId : item.id}`}>
              {item.externalId ? item.externalId : item.id}
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );
};

export default AppSidebarThreadsMenu;
