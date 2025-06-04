'use client';

import { Suspense } from 'react';

import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import ButtonSkeleton from '@/app/_ui/components/Button/ButtonSkeleton';
import SidebarBody from '@/app/_ui/components/Sidebar/SidebarBody';
import SidebarContent from '@/app/_ui/components/Sidebar/SidebarContent';
import SidebarGroup from '@/app/_ui/components/Sidebar/SidebarGroup';
import SidebarHeader from '@/app/_ui/components/Sidebar/SidebarHeader';
import SidebarNavigationButton from '@/app/_ui/components/Sidebar/SidebarNavigationButton';

import AppSidebarOrganizationDropdown from './AppSidebarOrganizationDropdown';

export interface AppSidebarContentProps {
  organizationSlug: string;
}

const AppSidebarContent = ({ organizationSlug }: AppSidebarContentProps) => {
  return (
    <SidebarContent className="bg-surface-muted border-border-muted border-r">
      <SidebarHeader className="h-12 justify-center">
        <Suspense fallback={<ButtonSkeleton size="lg" className="w-full" />}>
          <AppSidebarOrganizationDropdown />
        </Suspense>
      </SidebarHeader>
      <SidebarBody>
        <SidebarGroup>
          <SidebarNavigationButton
            size="sm"
            href={`/platform/${organizationSlug}/search`}
            isActiveRegex={new RegExp(`^/platform/${organizationSlug}/search`)}
          >
            <ButtonContent align="start">Search</ButtonContent>
          </SidebarNavigationButton>
          <SidebarNavigationButton
            size="sm"
            href={`/platform/${organizationSlug}/documents`}
            isActiveRegex={
              new RegExp(`^/platform/${organizationSlug}/documents`)
            }
          >
            <ButtonContent align="start">Documents</ButtonContent>
          </SidebarNavigationButton>
        </SidebarGroup>
      </SidebarBody>
    </SidebarContent>
  );
};

export default AppSidebarContent;
