import { schemaTask } from '@trigger.dev/sdk';
import { generateText } from 'ai';
import { z } from 'zod';

import openrouterProvider from '@/lib/openrouter/ai-provider';

export const extractRelevantInfoJob = schemaTask({
  id: 'extract-relevant-info',
  schema: z.object({
    userQuery: z.string(),
    searchQuery: z.string(),
    content: z.record(z.string(), z.unknown())
  }),
  run: async ({ userQuery, searchQuery, content }) => {
    const { text } = await generateText({
      model: openrouterProvider('openai/gpt-4o-mini'),
      messages: [
        {
          role: 'system',
          content: `You are an expert information extractor. Given the user's query, the search query that led to this search result, and the search result, extract all pieces of information that are relevant to answering the user's query. Return only the relevant context as plain text without commentary. If you don't find any relevant information, return an empty string.`
        },
        {
          role: 'user',
          content: `User query: ${userQuery}\nSearch query: ${searchQuery}\nSearch result: ${JSON.stringify(content)}`
        }
      ]
    });

    return {
      isRelevant: text !== '',
      relevantInfo: text
    };
  }
});
