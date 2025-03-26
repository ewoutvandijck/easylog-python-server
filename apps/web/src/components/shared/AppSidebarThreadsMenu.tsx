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
      {threads?.map((item) => (
        <SidebarMenuItem key={item.id}>
          <SidebarMenuButton
            asChild
            isActive={threadId === item.external_id || threadId === item.id}
            disabled={!isConnected}
          >
            <Link href={`/${item.external_id ? item.external_id : item.id}`}>
              {item.external_id ? item.external_id : item.id}
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );
};

export default AppSidebarThreadsMenu;
