import { cookies } from 'next/headers';

import SidebarProviderInner, {
  SidebarProviderInnerProps
} from './SidebarProviderInner';
import PersistentPanelsProvider from '../Panels/PersistentPanelsProvider';

export interface SidebarProviderProps extends SidebarProviderInnerProps {
  cookieName?: string;
  defaultLayout?: [number, number];
  className?: string;
}

const SidebarProvider = async ({
  children,
  cookieName = 'sidebar.layout',
  defaultLayout = [30, 70],
  className,
  ...props
}: React.PropsWithChildren<SidebarProviderProps>) => {
  const cookie = (await cookies()).get(cookieName);

  const layout = !cookie
    ? defaultLayout
    : (JSON.parse(cookie.value) as [number, number]);

  return (
    <PersistentPanelsProvider
      direction="horizontal"
      defaultLayout={layout}
      cookieName={cookieName}
      className={className}
    >
      <SidebarProviderInner {...props}>{children}</SidebarProviderInner>
    </PersistentPanelsProvider>
  );
};

export default SidebarProvider;
