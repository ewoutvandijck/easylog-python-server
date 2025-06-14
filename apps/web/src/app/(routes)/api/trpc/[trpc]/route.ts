import { fetchRequestHandler } from '@trpc/server/adapters/fetch';
import { NextRequest } from 'next/server';

import createTRPCContext from '@/lib/trpc/context';
import { appRouter } from '@/trpc-router';

export const maxDuration = 100;

const handler = async (req: NextRequest) => {
  return await fetchRequestHandler({
    endpoint: '/api/trpc',
    req,
    router: appRouter,
    createContext: async () => createTRPCContext(),
    onError: ({ error }) => {
      console.error(error);
    }
  });
};

export { handler as GET, handler as POST };
