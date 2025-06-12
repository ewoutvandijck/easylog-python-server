import { UIMessage, convertToModelMessages, streamText, tool } from 'ai';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import db from '@/database/client';
import openrouter from '@/lib/ai-providers/openrouter';
import createClient from '@/lib/easylog/client';

export const maxDuration = 30;

export const POST = async (req: NextRequest) => {
  const user = await getCurrentUser(req.headers);

  if (!user) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  const { messages }: { messages: UIMessage[] } = await req.json();

  const result = streamText({
    model: openrouter('openai/gpt-4.1'),
    system: `You're acting as a personal assistant and you're participating in a chat with ${user.name}. You're name is James, you're a male and you're from the UK. When you answer, you should always start with greeting the user by their name`,
    messages: convertToModelMessages(messages),
    tools: {
      easylogTest: tool({
        description: 'Test tool',
        parameters: z.object({}),
        execute: async () => {
          const account = await db.query.accounts.findFirst({
            where: {
              providerId: 'easylog',
              userId: user.id
            }
          });

          if (!account?.accessToken) {
            return {
              content: 'No access token'
            };
          }

          const client = createClient({
            apiKey: account.accessToken,
            basePath: 'https://staging2.easylog.nu/api'
          });

          try {
            const datasources = await client.default.v2ConfigurationGet();
            console.log(datasources);
          } catch (error) {
            console.error(error);

            return {
              error: error instanceof Error ? error.message : 'Unknown error'
            };
          }
        }
      })
    }
  });

  return result.toUIMessageStreamResponse();
};
