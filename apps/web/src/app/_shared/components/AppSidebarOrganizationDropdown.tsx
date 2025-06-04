'use client';

import { useSuspenseQuery } from '@tanstack/react-query';

import useOrganizationSlug from '@/app/_organizations/hooks/useOrganizationSlug';
import Typography from '@/app/_ui/components/Typography/Typography';
import useTRPC from '@/lib/trpc/browser';

const AppSidebarOrganizationDropdown = () => {
  const api = useTRPC();
  const organizationSlug = useOrganizationSlug();

  const { data: organization } = useSuspenseQuery(
    api.organizations.get.queryOptions({
      organizationId: organizationSlug
    })
  );

  return (
    <Typography variant="labelMd" className="truncate px-2">
      {organization.name}
    </Typography>
  );
};

export default AppSidebarOrganizationDropdown;
