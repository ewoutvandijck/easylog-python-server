'use client';

import Image from 'next/image';
import { useRouter } from 'next/navigation';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import DropdownMenu from '@/app/_ui/components/DropdownMenu/DropdownMenu';
import DropdownMenuContent from '@/app/_ui/components/DropdownMenu/DropdownMenuContent';
import DropdownMenuItem from '@/app/_ui/components/DropdownMenu/DropdownMenuItem';
import DropdownMenuTrigger from '@/app/_ui/components/DropdownMenu/DropdownMenuTrigger';
import type { User } from '@/database/schema';
import authBrowserClient from '@/lib/better-auth/browser';

export interface UserDropdownProps {
  user: User;
}

const UserDropdown = ({ user }: UserDropdownProps) => {
  const router = useRouter();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" shape="circle" className="p-0">
          <ButtonContent>
            <Image
              src={`https://ui-avatars.com/api/?name=${user.name}&background=267dc1&color=fff&size=64`}
              alt={user.name ?? 'User avatar'}
              width={32}
              height={32}
              className="size-8 rounded-full"
            />
          </ButtonContent>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        onClick={() => {
          void authBrowserClient.signOut({
            fetchOptions: {
              onSuccess: () => {
                router.push('/sign-in');
              }
            }
          });
        }}
      >
        <DropdownMenuItem>Uitloggen</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserDropdown;
