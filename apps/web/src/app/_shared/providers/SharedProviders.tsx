import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import Toaster from '@/app/_ui/components/Toaster/Toaster';

import TRPCReactProvider from './TRPCReactProvider';

const SharedProviders = async ({ children }: React.PropsWithChildren) => {
  return (
    <>
      <TRPCReactProvider>
        {children}
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-right"
        />
        <Toaster />
      </TRPCReactProvider>
    </>
  );
};

export default SharedProviders;
