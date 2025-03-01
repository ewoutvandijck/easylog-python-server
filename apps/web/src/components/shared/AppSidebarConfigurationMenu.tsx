'use client';
import { ChevronRight, MoreHorizontal, Plus } from 'lucide-react';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem
} from '../ui/sidebar';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '../ui/collapsible';
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger
} from '../ui/dropdown-menu';

import ConfigurationUpdateDialog from '../chat/ConfigurationUpdateDialog';
import useConfigurations from '@/hooks/use-configurations';

const AppSidebarConfigurationMenu = () => {
  const {
    configurations,
    activeConfiguration,
    setActiveConfiguration,
    addConfiguration
  } = useConfigurations();

  return (
    <>
      <Collapsible
        key="projects"
        title="Projects"
        defaultOpen
        className="group/collapsible"
      >
        <SidebarGroup className="p-0">
          <SidebarGroupLabel
            asChild
            className="group/label text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <CollapsibleTrigger>
              Configurations{' '}
              <ChevronRight className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-90" />
            </CollapsibleTrigger>
          </SidebarGroupLabel>
          <CollapsibleContent>
            <SidebarGroupContent>
              <SidebarMenu>
                {configurations.map((item) => (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton
                      className="cursor-pointer"
                      asChild
                      isActive={activeConfiguration?.name === item.name}
                      onClick={() => setActiveConfiguration(item.name)}
                    >
                      <span>{item.name}</span>
                    </SidebarMenuButton>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <SidebarMenuAction showOnHover>
                          <MoreHorizontal />
                          <span className="sr-only">More</span>
                        </SidebarMenuAction>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <ConfigurationUpdateDialog
                          configurationName={item.name}
                        >
                          <DropdownMenuItem
                            onSelect={(e) => e.preventDefault()}
                          >
                            <span>Update</span>
                          </DropdownMenuItem>
                        </ConfigurationUpdateDialog>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </CollapsibleContent>
        </SidebarGroup>
      </Collapsible>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            onClick={() =>
              addConfiguration({
                name: `Configuration ${configurations.length + 1}`,
                agentConfig: {
                  agent_class: 'OpenAIAssistant',
                  assistant_id: 'asst_1234567890'
                },
                easylogApiKey: '1234567890'
              })
            }
          >
            <Plus />
            <span>New Configuration</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </>
  );
};

export default AppSidebarConfigurationMenu;
