import SignInWithEasylog from '@/app/_auth/components/SignInWithEasylog';
import SignInWithUsernamePasswordForm from '@/app/_auth/components/SignInWithUsernamePassword';
import Card from '@/app/_ui/components/Card/Card';
import CardContent from '@/app/_ui/components/Card/CardContent';
import Typography from '@/app/_ui/components/Typography/Typography';

const SignInPage = async () => {
  return (
    <main className="container mx-auto flex min-h-dvh flex-col items-center justify-center gap-4">
      <Card shadow="none" className="w-full max-w-md">
        <CardContent>
          <Typography variant="headingMd">Sign in</Typography>
          <SignInWithEasylog />
          <SignInWithUsernamePasswordForm />
        </CardContent>
      </Card>
    </main>
  );
};

export default SignInPage;
