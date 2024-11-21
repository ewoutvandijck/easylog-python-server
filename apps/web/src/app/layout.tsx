import '../globals.css';

import type { Metadata } from 'next';
import { Toaster } from 'sonner';
import { inter } from '@/lib/fonts/fonts';
import Providers from '@/components/shared/Providers';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import AppSidebar from '@/components/shared/AppSidebar';

export const metadata: Metadata = {
  title: 'Easylog AI Chat',
  description: 'Easylog AI Chat'
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nl">
      <body className={`${inter.variable} antialiased font-sans`}>
        <Providers>
          <SidebarProvider>
            <AppSidebar />
            <SidebarInset>{children}</SidebarInset>
          </SidebarProvider>
        </Providers>
        <Toaster />
      </body>
    </html>
  );
}
