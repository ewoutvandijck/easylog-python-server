'use client';

import { IconArrowRight, IconMail } from '@tabler/icons-react';
import { AnimatePresence, motion } from 'motion/react';
import { useState } from 'react';
import { SubmitHandler } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import FormField from '@/app/_ui/components/FormField/FormField';
import FormFieldContent from '@/app/_ui/components/FormField/FormFieldContent';
import FormFieldError from '@/app/_ui/components/FormField/FormFieldError';
import FormFieldLabel from '@/app/_ui/components/FormField/FormFieldLabel';
import Input from '@/app/_ui/components/Input/Input';
import useZodForm from '@/app/_ui/hooks/useZodForm';
import authBrowserClient from '@/lib/better-auth/browser';

const signInWithUsernamePasswordSchema = z.object({
  email: z.string().email(),
  password: z.string()
});

type SignInWithUsernamePasswordSchema = z.infer<
  typeof signInWithUsernamePasswordSchema
>;

const SignInWithUsernamePasswordForm = () => {
  const [isFormVisible, setIsFormVisible] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors }
  } = useZodForm(signInWithUsernamePasswordSchema);

  const submitHandler: SubmitHandler<SignInWithUsernamePasswordSchema> = async (
    values
  ) => {
    const { error } = await authBrowserClient.signIn.email({
      email: values.email,
      password: values.password,
      callbackURL: '/chat'
    });

    if (error) {
      toast.error(error.message);
      throw error;
    }
  };

  return (
    <>
      <Button
        size="lg"
        onClick={() => setIsFormVisible(!isFormVisible)}
        isToggled={isFormVisible}
      >
        <ButtonContent iconLeft={IconMail}>
          Sign in with email and password
        </ButtonContent>
      </Button>

      <AnimatePresence>
        {isFormVisible && (
          <motion.form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit(submitHandler)}
            initial={{ height: 0, overflow: 'hidden' }}
            animate={{ height: 'auto', overflow: 'visible' }}
            exit={{ height: 0, overflow: 'hidden' }}
            transition={{
              duration: 0.3,
              ease: [0.4, 0, 0.2, 1]
            }}
          >
            <FormField>
              <FormFieldLabel asChild>
                <label htmlFor="email">Email address</label>
              </FormFieldLabel>
              <FormFieldContent>
                <Input
                  id="email"
                  tabIndex={1}
                  size="lg"
                  type="email"
                  placeholder="Email address"
                  autoFocus
                  autoComplete="email"
                  {...register('email')}
                />
                {errors.email && (
                  <FormFieldError>{errors.email.message}</FormFieldError>
                )}
              </FormFieldContent>
            </FormField>
            <FormField>
              <FormFieldLabel asChild>
                <label htmlFor="password">Password</label>
              </FormFieldLabel>
              <FormFieldContent>
                <Input
                  id="password"
                  tabIndex={2}
                  size="lg"
                  type="password"
                  placeholder="Password"
                  autoComplete="current-password"
                  {...register('password')}
                />
                {errors.password && (
                  <FormFieldError>{errors.password.message}</FormFieldError>
                )}
              </FormFieldContent>
            </FormField>
            <Button
              type="submit"
              size="lg"
              colorRole="brand"
              isDisabled={isSubmitting}
            >
              <ButtonContent
                iconRight={IconArrowRight}
                isLoading={isSubmitting}
              >
                Sign in
              </ButtonContent>
            </Button>
          </motion.form>
        )}
      </AnimatePresence>
    </>
  );
};

export default SignInWithUsernamePasswordForm;
