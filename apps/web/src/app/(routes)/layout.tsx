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
    <html
      lang="en"
      style={
        {
          '--chart-1': 'var(--color-chart-1)',
          '--chart-2': 'var(--color-chart-2)',
          '--chart-3': 'var(--color-chart-3)',
          '--chart-4': 'var(--color-chart-4)',
          '--chart-5': 'var(--color-chart-5)'
        } as React.CSSProperties
      }
    >
      <body
        className={`${inter.variable} flex min-h-svh flex-col subpixel-antialiased`}
      >
        <SharedProviders>{children}</SharedProviders>
      </body>
    </html>
  );
};

export default RootLayout;
