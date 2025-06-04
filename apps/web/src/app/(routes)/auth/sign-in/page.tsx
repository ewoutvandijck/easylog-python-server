import SignInWithGoogle from '@/app/_auth/components/SignInWithGoogle';

const SignInPage = async () => {
  return (
    <main className="container mx-auto flex min-h-dvh items-center justify-center">
      <SignInWithGoogle />
    </main>
  );
};

export default SignInPage;
