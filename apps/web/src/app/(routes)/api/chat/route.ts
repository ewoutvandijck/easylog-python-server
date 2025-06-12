import { UIMessage, convertToModelMessages, streamText } from 'ai';
import { NextRequest } from 'next/server';

import openrouter from '@/lib/ai-providers/openrouter';

export const maxDuration = 30;

export const POST = async (req: NextRequest) => {
  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: openrouter('openai/gpt-4.1'),
    messages: convertToModelMessages(messages)
  });

  return result.toUIMessageStreamResponse();
};
