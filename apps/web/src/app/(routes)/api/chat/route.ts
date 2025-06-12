import { UIMessage, convertToModelMessages, streamText } from 'ai';
import { NextRequest, NextResponse } from 'next/server';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import openrouter from '@/lib/ai-providers/openrouter';

export const maxDuration = 30;

export const POST = async (req: NextRequest) => {
  const user = await getCurrentUser(req.headers);

  if (!user) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  const { messages }: { messages: UIMessage[] } = await req.json();

  console.log(
    convertToModelMessages([
      {
        role: 'system',
        parts: [
          {
            type: 'text',
            text: `You're currently chatting with ${user.name}. When you answer, you should always start with greeting the user by their name`
          }
        ]
      },
      ...messages
    ])
  );

  const result = streamText({
    model: openrouter('openai/gpt-4.1'),
    system: `You're acting as a personal assistant and you're participating in a chat with ${user.name}. You're name is James, you're a male and you're from the UK. When you answer, you should always start with greeting the user by their name`,
    messages: convertToModelMessages(messages)
  });

  return result.toUIMessageStreamResponse();
};
