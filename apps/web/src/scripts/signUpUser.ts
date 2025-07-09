import authBrowserClient from '@/lib/better-auth/browser';

const signUpUser = async () => {
  const { data, error } = await authBrowserClient.signUp.email({
    email: 'demo@demo.com',
    password: 'DemoUser1!',
    name: 'Demo User'
  });

  if (error) {
    console.error(error);
    throw error;
  }

  console.log(data);
};

void signUpUser();
