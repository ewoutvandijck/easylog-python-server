import AppSidebar from '@/components/chat/AppSidebar';
import { Button } from '@/components/ui/button';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

export default function Home() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <Button>Click me</Button>
      </SidebarInset>
    </SidebarProvider>
  );
}
