import { cookies } from 'next/headers';

import SidebarProviderInner from './SidebarProviderInner';

export interface SidebarProviderProps {
  cookieName: string;
}

const SidebarProvider = async ({
  cookieName,
  children
}: React.PropsWithChildren<SidebarProviderProps>) => {
  const initialWidth = (await cookies()).get(`${cookieName}.width`)?.value;

  const initialIsCollapsed = (await cookies()).get(
    `${cookieName}.is-collapsed`
  )?.value;

  return (
    <SidebarProviderInner
      cookieName={cookieName}
      initialWidth={initialWidth ? Number(initialWidth) : 250}
      initialIsCollapsed={
        initialIsCollapsed ? initialIsCollapsed === 'true' : false
      }
    >
      {children}
    </SidebarProviderInner>
  );
};

export default SidebarProvider;
