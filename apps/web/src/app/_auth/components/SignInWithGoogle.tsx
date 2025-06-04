'use client';

import { useMutation } from '@tanstack/react-query';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import IconGoogle from '@/app/_ui/components/Icon/IconGoogle';
import authBrowserClient from '@/lib/better-auth/browser';

const SignInWithGoogle = () => {
  const { mutate: signInWithGoogle, isPending } = useMutation({
    mutationFn: () =>
      authBrowserClient.signIn.social({
        provider: 'google',
        callbackURL: '/platform'
      })
  });

  return (
    <Button size="lg" onClick={() => signInWithGoogle()} isDisabled={isPending}>
      <ButtonContent iconLeft={IconGoogle} isLoading={isPending}>
        Sign in with Google
      </ButtonContent>
    </Button>
  );
};

export default SignInWithGoogle;
