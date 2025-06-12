'use client';

import { useMutation } from '@tanstack/react-query';
import { useEffect } from 'react';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import LogoIcon from '@/app/_ui/components/Logo/LogoIcon';
import authBrowserClient from '@/lib/better-auth/browser';

const SignInWithEasylog = () => {
  const { mutate: signInWithEasylog, isPending } = useMutation({
    mutationFn: () =>
      authBrowserClient.signIn.oauth2({
        providerId: 'easylog',
        callbackURL: '/chat'
      })
  });

  useEffect(() => {
    signInWithEasylog();
  }, [signInWithEasylog]);

  return (
    <Button
      size="lg"
      onClick={() => signInWithEasylog()}
      isDisabled={isPending}
    >
      <ButtonContent iconLeft={LogoIcon} isLoading={isPending}>
        Inloggen met Apperto
      </ButtonContent>
    </Button>
  );
};

export default SignInWithEasylog;
