import {
  UIMessage,
  convertToModelMessages,
  createIdGenerator,
  createUIMessageStream,
  createUIMessageStreamResponse,
  streamText,
  tool
} from 'ai';
import { eq } from 'drizzle-orm';
import { NextRequest, NextResponse } from 'next/server';
import z from 'zod';

import agentConfigSchema from '@/app/_agents/schemas/agentConfigSchema';
import getCurrentUser from '@/app/_auth/data/getCurrentUser';
import internalChartConfigSchema from '@/app/_charts/schemas/internalChartConfigSchema';
import toolCreateMultipleAllocations from '@/app/_chats/tools/easylog-backend/toolCreateMultipleAllocations';
import toolCreatePlanningPhase from '@/app/_chats/tools/easylog-backend/toolCreatePlanningPhase';
import toolCreatePlanningProject from '@/app/_chats/tools/easylog-backend/toolCreatePlanningProject';
import toolDeleteAllocation from '@/app/_chats/tools/easylog-backend/toolDeleteAllocation';
import toolGetDataSources from '@/app/_chats/tools/easylog-backend/toolGetDataSources';
import toolGetPlanningPhase from '@/app/_chats/tools/easylog-backend/toolGetPlanningPhase';
import toolGetPlanningPhases from '@/app/_chats/tools/easylog-backend/toolGetPlanningPhases';
import toolGetPlanningProject from '@/app/_chats/tools/easylog-backend/toolGetPlanningProject';
import toolGetPlanningProjects from '@/app/_chats/tools/easylog-backend/toolGetPlanningProjects';
import toolGetProjectsOfResource from '@/app/_chats/tools/easylog-backend/toolGetProjectsOfResource';
import toolGetResourceGroups from '@/app/_chats/tools/easylog-backend/toolGetResourceGroups';
import toolGetResources from '@/app/_chats/tools/easylog-backend/toolGetResources';
import toolUpdateMultipleAllocations from '@/app/_chats/tools/easylog-backend/toolUpdateMultipleAllocations';
import toolUpdatePlanningPhase from '@/app/_chats/tools/easylog-backend/toolUpdatePlanningPhase';
import toolUpdatePlanningProject from '@/app/_chats/tools/easylog-backend/toolUpdatePlanningProject';
import toolExecuteSQL from '@/app/_chats/tools/toolExecuteSQL';
import toolLoadDocument from '@/app/_chats/tools/toolLoadDocument';
import toolSearchKnowledgeBase from '@/app/_chats/tools/toolSearchKnowledgeBase';
import db from '@/database/client';
import { chats } from '@/database/schema';
import openrouter from '@/lib/ai-providers/openrouter';
import isUUID from '@/utils/is-uuid';

export const maxDuration = 800;

export const POST = async (
  req: NextRequest,
  { params }: { params: Promise<{ agentSlug: string }> }
) => {
  const { agentSlug } = await params;

  const user = await getCurrentUser(req.headers);

  if (!user) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  const { message, id }: { message: UIMessage; id: string } = await req.json();

  const chat = await db.query.chats.findFirst({
    where: {
      id,
      userId: user.id
    },
    with: {
      agent: true
    }
  });

  if (
    !chat ||
    (isUUID(agentSlug) && chat.agentId !== agentSlug) ||
    (!isUUID(agentSlug) && chat.agent.slug !== agentSlug)
  ) {
    return new NextResponse('Chat not found', { status: 404 });
  }

  const schema = agentConfigSchema.safeParse(chat.agent.config);

  if (!schema.success) {
    return new NextResponse('Invalid agent config', { status: 400 });
  }

  const promptWithContext = schema.data.prompt
    .replaceAll('{{user.name}}', user.name ?? 'Unknown')
    .replaceAll('{{agent.name}}', chat.agent.name)
    .replaceAll('{{now}}', new Date().toISOString());

  const messages = [...(chat.messages as UIMessage[]), message];

  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const result = streamText({
        model: openrouter(chat.agent.config.model),
        system: promptWithContext,
        messages: convertToModelMessages(messages),
        tools: {
          createChart: tool({
            description: 'Create a chart',
            inputSchema: internalChartConfigSchema,
            execute: async (config, opts) => {
              writer.write({
                type: 'data-chart',
                id: opts.toolCallId,
                data: config
              });

              return 'Chart created';
            }
          }),
          getDatasources: toolGetDataSources(user.id),
          getPlanningProjects: toolGetPlanningProjects(user.id),
          getPlanningProject: toolGetPlanningProject(user.id),
          createPlanningProject: toolCreatePlanningProject(user.id),
          updatePlanningProject: toolUpdatePlanningProject(user.id),
          getPlanningPhases: toolGetPlanningPhases(user.id),
          getPlanningPhase: toolGetPlanningPhase(user.id),
          updatePlanningPhase: toolUpdatePlanningPhase(user.id),
          createPlanningPhase: toolCreatePlanningPhase(user.id),
          getResources: toolGetResources(user.id),
          getProjectsOfResource: toolGetProjectsOfResource(user.id),
          getResourceGroups: toolGetResourceGroups(user.id),
          createMultipleAllocations: toolCreateMultipleAllocations(user.id),
          updateMultipleAllocations: toolUpdateMultipleAllocations(user.id),
          deleteAllocation: toolDeleteAllocation(user.id),
          executeSql: toolExecuteSQL(),
          searchKnowledgeBase: toolSearchKnowledgeBase(
            {
              agentId: chat.agentId
            },
            writer
          ),
          loadDocument: toolLoadDocument(),
          clearChat: tool({
            description: 'Clear the chat',
            inputSchema: z.object({}),
            execute: async () => {
              await db.insert(chats).values({
                agentId: chat.agentId,
                userId: user.id
              });

              return 'Chat cleared';
            }
          })
        }
      });

      writer.merge(result.toUIMessageStream({}));
    },
    generateId: createIdGenerator({
      prefix: 'msg',
      size: 16
    }),
    originalMessages: messages,
    onFinish: async ({ messages }) => {
      // Remove duplicate message ids, keeping only the last occurrence of each id
      const seenIds = new Set<string>();
      const dedupedMessages: typeof messages = [];

      // Iterate from end to start to keep the last occurrence
      for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i];
        if (!seenIds.has(msg.id)) {
          seenIds.add(msg.id);
          dedupedMessages.unshift(msg);
        }
      }
      // Replace messages with dedupedMessages for downstream usage
      messages = dedupedMessages;

      await db
        .update(chats)
        .set({
          messages
        })
        .where(eq(chats.id, id));
    }
  });

  return createUIMessageStreamResponse({ stream });
};
