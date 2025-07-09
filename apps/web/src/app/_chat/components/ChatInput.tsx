'use client';

import { useChat } from '@ai-sdk/react';
import { IconArrowUp } from '@tabler/icons-react';
import { motion } from 'motion/react';
import { useEffect, useRef } from 'react';
import { SubmitHandler } from 'react-hook-form';
import TextareaAutosize from 'react-textarea-autosize';
import { z } from 'zod';

import Button from '@/app/_ui/components/Button/Button';
import ButtonContent from '@/app/_ui/components/Button/ButtonContent';
import Icon from '@/app/_ui/components/Icon/Icon';
import IconSpinner from '@/app/_ui/components/Icon/IconSpinner';
import useZodForm from '@/app/_ui/hooks/useZodForm';

import useChatContext from '../hooks/useChatContext';

const schema = z.object({
  content: z.string().min(1)
});

const ChatInput = () => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { chat } = useChatContext();

  const { sendMessage } = useChat({
    chat
  });

  const {
    reset,
    register,
    handleSubmit,
    formState: { isSubmitting, isValid, isSubmitSuccessful }
  } = useZodForm(schema);

  const submitHandler: SubmitHandler<z.infer<typeof schema>> = async (data) => {
    await sendMessage({
      parts: [{ type: 'text', text: data.content }],
      role: 'user'
    });
  };

  const { ref: textareaFormRef, ...rest } = register('content');

  useEffect(() => {
    if (isSubmitSuccessful) {
      reset();
      textareaRef.current?.focus();
    }
  }, [isSubmitSuccessful, reset]);

  return (
    <motion.div
      className="sticky bottom-3 left-0 right-0 px-3 md:bottom-5 md:px-5"
      initial={{ opacity: 0, y: '50%', filter: 'blur(5px)' }}
      animate={{
        opacity: 1,
        y: 0,

        filter: 'blur(0px)',
        transition: {
          delay: 0.3,
          duration: 0.5,
          ease: [0.22, 1, 0.36, 1]
        }
      }}
    >
      <div className="bg-surface-primary shadow-short mx-auto w-full max-w-2xl overflow-clip rounded-2xl bg-clip-padding contain-inline-size">
        <div
          className="cursor-text px-5 pt-5 data-[disabled=true]:cursor-not-allowed data-[disabled=true]:opacity-50"
          data-disabled={isSubmitting}
          onClick={() => {
            textareaRef.current?.focus();
          }}
        >
          <TextareaAutosize
            disabled={isSubmitting}
            autoFocus
            className="decoration-none placeholder:text-text-muted text-text-primary w-full resize-none focus:outline-none"
            ref={(e) => {
              textareaFormRef(e);
              textareaRef.current = e;
            }}
            onKeyDown={(e) => {
              if (!e.shiftKey && e.key === 'Enter') {
                e.preventDefault();
                void handleSubmit(submitHandler)();
              }
            }}
            minRows={1}
            maxRows={6}
            placeholder="Ask me anything..."
            {...rest}
          />
        </div>

        <div className="flex items-center justify-end px-2.5 pb-2.5">
          <Button
            shape="circle"
            size="lg"
            isDisabled={isSubmitting || !isValid}
            onClick={handleSubmit(submitHandler)}
          >
            <ButtonContent>
              <Icon icon={isSubmitting ? IconSpinner : IconArrowUp} />
            </ButtonContent>
          </Button>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatInput;
