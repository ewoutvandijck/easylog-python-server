import {
  QueryClient,
  defaultShouldDehydrateQuery,
  isServer
} from '@tanstack/react-query';
import { cache } from 'react';
import { deserialize, serialize } from 'superjson';

const createQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000
      },
      dehydrate: {
        serializeData: serialize,
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) || query.state.status === 'pending'
      },
      hydrate: {
        deserializeData: deserialize
      }
    }
  });
};

let browserQueryClient: QueryClient | undefined = undefined;

const getQueryClient = cache(() => {
  if (isServer) {
    return createQueryClient();
  }

  if (!browserQueryClient) {
    browserQueryClient = createQueryClient();
  }

  return browserQueryClient;
});

export default getQueryClient;
