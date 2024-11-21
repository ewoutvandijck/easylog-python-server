'use client';

import { ChevronsLeftRightEllipsis, ChevronsUpDown, Plus } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar
} from '@/components/ui/sidebar';

import useConnections from '@/hooks/use-connections';
import useIsConnectionHealthy from '@/hooks/use-is-connection-healthy';
import { cn } from '@/lib/utils';
import ConnectionAddDialog from './ConnectionAddDialog';

const ConnectionSwitcher = () => {
  const { activeConnection, connections, setActiveConnection } =
    useConnections();
  const { isMobile } = useSidebar();

  const { data: isHealthy } = useIsConnectionHealthy();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary">
                <ChevronsLeftRightEllipsis
                  className={cn(
                    'size-4',
                    isHealthy ? 'text-green-400' : 'text-red-400 animate-pulse'
                  )}
                />
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">
                  {activeConnection.name}
                </span>
                <span className="truncate text-xs">{activeConnection.url}</span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            align="start"
            side={isMobile ? 'bottom' : 'right'}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Connections
            </DropdownMenuLabel>
            {connections.map((connection, i) => (
              <DropdownMenuItem
                key={`${connection.name}-${i}`}
                onClick={() => setActiveConnection(connection.name)}
                className={cn(
                  'gap-2 p-2 cursor-pointer',
                  activeConnection.name === connection.name &&
                    'bg-sidebar-accent'
                )}
              >
                {connection.name}
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <ConnectionAddDialog>
              <DropdownMenuItem
                className="gap-2 p-2 w-full"
                onSelect={(e) => {
                  e.preventDefault();
                }}
              >
                <div className="flex size-6 items-center justify-center rounded-md border bg-background">
                  <Plus className="size-4" />
                </div>
                <div className="font-medium text-muted-foreground">
                  Add connection
                </div>
              </DropdownMenuItem>
            </ConnectionAddDialog>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};

export default ConnectionSwitcher;
