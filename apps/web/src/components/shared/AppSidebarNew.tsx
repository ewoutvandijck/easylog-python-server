import { SquarePen } from 'lucide-react';
import { SidebarMenu, SidebarMenuItem, SidebarGroup } from '../ui/sidebar';
import { Button } from '../ui/button';
import useIsConnectionHealthy from '@/hooks/use-is-connection-healthy';
import ChatNewDialog from '../chat/ChatNewDialog';

const AppSidebarNew = () => {
  const { data: isConnected } = useIsConnectionHealthy();

  return (
    <SidebarGroup>
      <SidebarMenu>
        <SidebarMenuItem>
          <ChatNewDialog>
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              disabled={!isConnected}
            >
              <SquarePen />
              <span>New Chat</span>
            </Button>
          </ChatNewDialog>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
};

export default AppSidebarNew;
