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
    model: openrouter('anthropic/claude-sonnet-4'),
    system: `You're acting as a personal assistant and you're participating in a chat with ${user.name}. When first starting the conversation, you should greet the user by their first name.`,
    messages: convertToModelMessages(messages),
    tools: {
      getDatasources: tool({
        description: 'Get all datasources from Easylog',
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

          const datasources = await client.datasources.v2DatasourcesGet();

          return {
            content: JSON.stringify(datasources, null, 2)
          };
        }
      })
    }
  });

  return result.toUIMessageStreamResponse();
};
