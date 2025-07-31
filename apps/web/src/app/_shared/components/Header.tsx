import Link from 'next/link';

import Logo from '@/app/_ui/components/Logo/Logo';
import type { User } from '@/database/schema';

import UserDropdown from './UserDropdown';

export interface HeaderProps {
  user: User;
  agentSlug: string;
}

const Header = ({ user, agentSlug }: HeaderProps) => {
  return (
    <div className="bg-surface-primary border-border-muted sticky top-0 z-10 flex h-12 border-b">
      <div className="container flex items-center justify-between">
        <Link href="/chat">
          <Logo className="h-10 w-auto" />
        </Link>
        <UserDropdown user={user} agentId={agentSlug} />
      </div>
    </div>
  );
};

export default Header;
