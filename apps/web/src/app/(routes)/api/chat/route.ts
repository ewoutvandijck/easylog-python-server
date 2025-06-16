import {
  UIMessage,
  convertToModelMessages,
  createUIMessageStream,
  createUIMessageStreamResponse,
  streamText,
  tool
} from 'ai';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import internalChartConfigSchema from '@/app/_charts/schemas/internalChartConfigSchema';
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

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const result = streamText({
        model: openrouter('openai/gpt-4.1'),
        system: `You're acting as a personal assistant and you're participating in a chat with ${user.name}. When first starting the conversation, you should greet the user by their first name.`,
        messages: convertToModelMessages(messages),
        tools: {
          createChart: tool({
            description: 'Create a chart',
            parameters: internalChartConfigSchema,
            execute: async (config, { toolCallId }) => {
              writer.write({
                type: 'data-chart',
                id: toolCallId,
                data: config
              });
              return true;
            }
          }),
          getDatasources: tool({
            description: 'Get all datasources from Easylog',
            parameters: z.object({
              types: z.array(z.string()).optional().default([])
            }),
            execute: async ({ types }) => {
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

              const datasources = await client.datasources.v2DatasourcesGet({
                types
              });

              return JSON.stringify(datasources, null, 2);
            }
          })
        }
      });

      writer.merge(result.toUIMessageStream());
    }
  });

  return createUIMessageStreamResponse({ stream });
};
