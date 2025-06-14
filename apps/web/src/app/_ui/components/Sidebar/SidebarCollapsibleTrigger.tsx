'use client';

import { CollapsibleTriggerProps } from '@radix-ui/react-collapsible';
import { IconChevronRight } from '@tabler/icons-react';

import SidebarMenuButton from './SidebarMenuButton';
import SidebarMenuButtonContent from './SidebarMenuButtonContent';
import CollapsibleTrigger from '../Collapsible/CollapsilbeTrigger';
import { ContentWrapperProps } from '../ContentWrapper/ContentWrapper';
import Icon from '../Icon/Icon';

export interface SidebarCollapsibleTriggerProps
  extends CollapsibleTriggerProps {
  contentRight?: ContentWrapperProps['contentRight'];
}

const SidebarCollapsibleTrigger = ({
  contentRight,
  children
}: React.PropsWithChildren<SidebarCollapsibleTriggerProps>) => {
  return (
    <CollapsibleTrigger asChild>
      <SidebarMenuButton className="group w-full grow text-xs text-text-muted">
        <SidebarMenuButtonContent
          contentRight={contentRight}
          contentLeft={
            <Icon
              icon={IconChevronRight}
              className="w-5 transition-transform group-data-[state=open]:rotate-90"
            />
          }
          align="start"
        >
          {children}
        </SidebarMenuButtonContent>
      </SidebarMenuButton>
    </CollapsibleTrigger>
  );
};

export default SidebarCollapsibleTrigger;
