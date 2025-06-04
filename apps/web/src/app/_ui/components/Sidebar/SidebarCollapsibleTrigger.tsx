'use client';

import { CollapsibleTriggerProps } from '@radix-ui/react-collapsible';
import { IconChevronRight } from '@tabler/icons-react';

import SidebarButton from './SidebarButton';
import ButtonContent from '../Button/ButtonContent';
import CollapsibleTrigger from '../Collapsible/CollapsilbeTrigger';
import Icon from '../Icon/Icon';

export interface SidebarCollapsibleTriggerProps
  extends CollapsibleTriggerProps {}

const SidebarCollapsibleTrigger = ({
  children
}: React.PropsWithChildren<SidebarCollapsibleTriggerProps>) => {
  return (
    <CollapsibleTrigger asChild>
      <SidebarButton className="text-text-primary-on-fill/75 group w-full grow text-xs">
        <ButtonContent
          contentRight={
            <Icon
              icon={IconChevronRight}
              className="w-5 transition-transform group-data-[state=open]:rotate-90"
            />
          }
          align="start"
        >
          {children}
        </ButtonContent>
      </SidebarButton>
    </CollapsibleTrigger>
  );
};

export default SidebarCollapsibleTrigger;
