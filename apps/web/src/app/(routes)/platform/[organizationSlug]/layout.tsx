import { HydrationBoundary, dehydrate } from '@tanstack/react-query';
import { notFound } from 'next/navigation';

import AppSidebarContent from '@/app/_shared/components/AppSidebarContent';
import SidebarDesktop from '@/app/_ui/components/Sidebar/SidebarDesktop';
import SidebarMobile from '@/app/_ui/components/Sidebar/SidebarMobile';
import SidebarProvider from '@/app/_ui/components/Sidebar/SidebarProvider';
import getQueryClient from '@/lib/react-query';
import api from '@/lib/trpc/server';
import tryCatch from '@/utils/try-catch';

const PlatformLayout = async ({
  children,
  params
}: React.PropsWithChildren<{
  params: Promise<{ organizationSlug: string }>;
}>) => {
  const { organizationSlug } = await params;

  const queryClient = getQueryClient();

  const [[organization], [me]] = await Promise.all([
    tryCatch(
      queryClient.fetchQuery(
        api.organizations.get.queryOptions({
          organizationId: organizationSlug
        })
      )
    ),
    tryCatch(queryClient.fetchQuery(api.auth.getMe.queryOptions()))
  ]);

  if (
    !organization ||
    !me ||
    !me.organizations.some((o) => o.id === organization.id)
  ) {
    notFound();
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="relative z-10 h-dvh overflow-hidden">
        <div className="flex h-full w-full">
          <SidebarProvider cookieName="deep-research.sidebar-width">
            <SidebarDesktop>
              <AppSidebarContent organizationSlug={organizationSlug} />
            </SidebarDesktop>
            <SidebarMobile>
              <AppSidebarContent organizationSlug={organizationSlug} />
            </SidebarMobile>
            <div className="bg-surface-primary relative flex h-full min-h-dvh w-full flex-1 flex-col overflow-y-scroll">
              {children}
            </div>
          </SidebarProvider>
        </div>
      </div>
    </HydrationBoundary>
  );
};

export default PlatformLayout;
