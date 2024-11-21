'use client';
import {
  ChevronRight,
  Folder,
  Forward,
  MoreHorizontal,
  Plus,
  Trash2
} from 'lucide-react';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar
} from '../ui/sidebar';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from '../ui/collapsible';
import {
  DropdownMenu,
  DropdownMenuSeparator,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger
} from '../ui/dropdown-menu';
import { Separator } from '../ui/separator';

const projects = [
  {
    name: 'Project 1',
    url: '/project/1',
    icon: Folder
  },
  {
    name: 'Project 2',
    url: '/project/2',
    icon: Folder
  }
];

const AppSidebarConfigurationMenu = () => {
  const { isMobile } = useSidebar();

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
                {projects.map((item) => (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton asChild isActive={false}>
                      <a href={item.url}>{item.name}</a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </CollapsibleContent>
        </SidebarGroup>
      </Collapsible>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton>
            <Plus />
            <span>New Configuration</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </>

    // <SidebarGroup className="group-data-[collapsible=icon]:hidden">
    //   <SidebarGroupLabel>Projects</SidebarGroupLabel>
    //   <SidebarMenu>
    //     <Collapsible
    //       key="projects"
    //       asChild
    //       defaultOpen={true}
    //       className="group/collapsible"
    //     >
    //       <SidebarMenuItem>
    //         <CollapsibleTrigger asChild>
    //           <SidebarMenuButton tooltip="Projects">
    //             <Folder />
    //             <span>Projects</span>
    //             <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
    //           </SidebarMenuButton>
    //         </CollapsibleTrigger>
    //         <CollapsibleContent>
    //           <SidebarMenuSub>
    //             {projects.map((item) => (
    //               <SidebarMenuSubItem key={item.name}>
    //                 <SidebarMenuSubButton asChild>
    //                   <a href={item.url}>
    //                     <item.icon />
    //                     <span>{item.name}</span>
    //                   </a>
    //                 </SidebarMenuSubButton>
    //                 <DropdownMenu>
    //                   <DropdownMenuTrigger asChild>
    //                     <SidebarMenuAction showOnHover>
    //                       <MoreHorizontal />
    //                       <span className="sr-only">More</span>
    //                     </SidebarMenuAction>
    //                   </DropdownMenuTrigger>
    //                   <DropdownMenuContent
    //                     className="w-48 rounded-lg"
    //                     side={isMobile ? 'bottom' : 'right'}
    //                     align={isMobile ? 'end' : 'start'}
    //                   >
    //                     <DropdownMenuItem>
    //                       <Folder className="text-muted-foreground" />
    //                       <span>View Project</span>
    //                     </DropdownMenuItem>
    //                     <DropdownMenuItem>
    //                       <Forward className="text-muted-foreground" />
    //                       <span>Share Project</span>
    //                     </DropdownMenuItem>
    //                     <DropdownMenuSeparator />
    //                     <DropdownMenuItem>
    //                       <Trash2 className="text-muted-foreground" />
    //                       <span>Delete Project</span>
    //                     </DropdownMenuItem>
    //                   </DropdownMenuContent>
    //                 </DropdownMenu>
    //               </SidebarMenuSubItem>
    //             ))}
    //           </SidebarMenuSub>
    //         </CollapsibleContent>
    //       </SidebarMenuItem>
    //     </Collapsible>
    //   </SidebarMenu>
    // </SidebarGroup>
  );
};

export default AppSidebarConfigurationMenu;
