import { AbortTaskRunError, logger, schemaTask } from '@trigger.dev/sdk';
import { generateObject, generateText } from 'ai';
import { z } from 'zod';

import db from '@/database/client';
import openrouterProvider from '@/lib/openrouter/ai-provider';
import getDocumentsCollection from '@/lib/weaviate/collections/documents';

import { extractRelevantInfoJob } from './extract-relevant-info-job';

export const runDeepResearchJob = schemaTask({
  id: 'run-deep-research',
  schema: z.object({
    userQuery: z.string(),
    organizationId: z.string()
  }),
  run: async ({ userQuery, organizationId }) => {
    const {
      object: { searchQueries }
    } = await generateObject({
      model: openrouterProvider('openai/gpt-4o-mini'),
      prompt: `You are an expert research assistant. Given the user's query, generate up to 5 distinct, precise search queries that would help gather comprehensive information on the topic in English. The user's query is: ${userQuery}`,
      schema: z.object({
        searchQueries: z.array(z.string()).min(1).max(5)
      })
    });

    logger.info('Search queries', { searchQueries });

    const collection = await getDocumentsCollection();

    const searchResults = await Promise.all(
      searchQueries.map(async (searchQuery) => {
        const searchResult = await collection.query.hybrid(searchQuery, {
          limit: 10,
          alpha: 0.5,
          autoLimit: 1,
          returnMetadata: 'all',
          filters: collection.filter
            .byProperty('organizationId')
            .equal(organizationId)
        });

        return {
          query: searchQuery,
          ...searchResult
        };
      })
    );

    const uniqueSearchResults = searchResults
      .flat()
      .flatMap((result) =>
        result.objects.map((object) => ({
          query: result.query,
          ...object
        }))
      )
      .sort((a, b) => (b.metadata?.score ?? 0) - (a.metadata?.score ?? 0))
      .filter(
        (result, index, self) =>
          index === self.findIndex((t) => t.uuid === result.uuid)
      );

    if (!uniqueSearchResults.length) {
      throw new AbortTaskRunError('No search results found');
    }

    logger.info('Search results', { uniqueSearchResults });

    const documents = await db.query.documents.findMany({
      where: {
        organizationId,
        vectorDocumentId: {
          in: uniqueSearchResults.map(({ uuid }) => uuid)
        }
      }
    });

    if (!documents.length) {
      throw new AbortTaskRunError('No documents found');
    }

    const relevantInfoResults =
      await extractRelevantInfoJob.batchTriggerAndWait(
        uniqueSearchResults
          .map((searchResult) => ({
            ...searchResult,
            content: documents.find(
              ({ vectorDocumentId }) => vectorDocumentId === searchResult.uuid
            )?.content
          }))
          .filter(({ content }) => content !== undefined)
          .map(({ query: searchQuery, ...searchResult }) => ({
            payload: {
              userQuery,
              searchQuery,
              content: searchResult.content as Record<string, unknown>
            }
          }))
      );

    const relevantInfo = relevantInfoResults.runs
      .map((result) => {
        if (!result.ok || !result.output.isRelevant) {
          return null;
        }

        return result.output;
      })
      .filter(Boolean) as { relevantInfo: string }[];

    logger.info('Relevant info', { relevantInfo });

    const searchResultReport = await generateText({
      model: openrouterProvider('openai/gpt-4o-mini'),
      messages: [
        {
          role: 'system',
          content: `You are an expert researcher and report writer. Based on the gathered contexts below and the original query, write a comprehensive, well-structured, and detailed report that addresses the query thoroughly. Include all relevant insights and conclusions without extraneous commentary.`
        },
        {
          role: 'user',
          content: `User query: ${userQuery}\nGathered contexts: ${JSON.stringify(
            relevantInfo.map((info) => ({ context: info.relevantInfo })),
            null,
            2
          )}`
        }
      ]
    });

    logger.info(searchResultReport.text);

    return {
      searchQueries,
      searchResults: uniqueSearchResults,
      relevantInfo,
      searchResultReport: searchResultReport.text
    };
  }
});
