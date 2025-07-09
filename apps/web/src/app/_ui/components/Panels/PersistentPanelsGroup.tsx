import { cookies } from 'next/headers';

import PersistentPanelsProvider from './PersistentPanelsProvider';
import { ResizablePanelGroupProps } from '../Resizable/ResizablePanelGroup';

export interface PersistentPanelsGroupProps {
  cookieName?: string;
  defaultLayout?: number[];
}

const PersistentPanelsGroup = async ({
  children,
  cookieName = 'panels.layout',
  defaultLayout = [30, 30, 40],
  ...props
}: React.PropsWithChildren<
  PersistentPanelsGroupProps & ResizablePanelGroupProps
>) => {
  const cookie = (await cookies()).get(cookieName);

  const layout = !cookie
    ? defaultLayout
    : (JSON.parse(cookie.value) as [number, number]);

  return (
    <PersistentPanelsProvider
      cookieName={cookieName}
      defaultLayout={layout}
      {...props}
    >
      {children}
    </PersistentPanelsProvider>
  );
};

export default PersistentPanelsGroup;
