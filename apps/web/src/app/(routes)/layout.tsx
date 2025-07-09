import '../globals.css';

import type { Metadata } from 'next';

import inter from '@/lib/fonts/inter';

import SharedProviders from '../_shared/providers/SharedProviders';

export const metadata: Metadata = {
  title: 'Apperto',
  description: 'Apperto AI Chat'
};

const RootLayout = ({ children }: React.PropsWithChildren) => {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} flex min-h-svh flex-col subpixel-antialiased`}
      >
        <SharedProviders>{children}</SharedProviders>
      </body>
    </html>
  );
};

export default RootLayout;
