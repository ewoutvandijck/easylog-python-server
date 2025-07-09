'use client';

import { Suspense, useEffect, useState } from 'react';

export interface BrowserOnlySuspenseProps {
  fallback?: React.ReactNode;
}

/**
 * `BrowserOnlySuspense` is a utility component designed to prevent Server-Side
 * Rendering (SSR) errors arising from child components that depend on
 * client-side only data.
 *
 * **Problem Scenario**: For instance, when certain components need to access
 * user data, they might trigger a `getMe` request. If this request is made
 * during SSR, it can fail because the necessary cookie isn't present on the
 * server side. This failure can lead to hydration errors when React attempts to
 * reconcile the server-rendered content with the client-rendered content.
 *
 * **Solution**: This component addresses the issue by ensuring that its
 * children are only rendered once the application has been mounted on the
 * client. Until then, it renders a fallback component or UI to indicate loading
 * or placeholder state.
 *
 * @example
 *   <BrowserOnlySuspense fallback={<LoadingSpinner />}>
 *     <UserSpecificComponent />
 *   </BrowserOnlySuspense>;
 *
 * @param fallback - The content to render while waiting for client-side mount.
 * @param children - Child components that rely on client-side only data.
 * @returns Renders the `fallback` content until the client side is ready, then
 *   renders the child components wrapped within a `Suspense` component.
 */
const BrowserOnlySuspense = ({
  fallback = null,
  children
}: React.PropsWithChildren<BrowserOnlySuspenseProps>) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <>{fallback}</>;
  }

  return <Suspense fallback={fallback}>{children}</Suspense>;
};

export default BrowserOnlySuspense;
