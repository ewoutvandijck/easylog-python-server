import { headers } from 'next/headers';
import { forbidden } from 'next/navigation';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import Header from '@/app/_shared/components/Header';

const PlatformLayout = async ({ children }: React.PropsWithChildren) => {
  const user = await getCurrentUser(await headers());

  if (!user) {
    throw forbidden();
  }

  return (
    <main className="flex h-svh flex-col">
      <Header user={user} />
      {children}
    </main>
  );
};

export default PlatformLayout;
