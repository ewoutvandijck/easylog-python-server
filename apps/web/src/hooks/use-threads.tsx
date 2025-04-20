import { useInfiniteQuery } from '@tanstack/react-query';
import useApiClient from './use-api-client';

const useThreads = () => {
  const { threads, activeConnection } = useApiClient();
  return useInfiniteQuery({
    queryKey: ['threads', activeConnection.name],
    queryFn: async ({ pageParam = 0 }) => {
      try {
        const response = await threads.getThreadsThreadsGet({
          limit: 5,
          offset: pageParam,
          order: 'desc'
        });

        return response.data;
      } catch (error) {
        console.error(error);
        throw error;
      }
    },
    getNextPageParam: (lastPage, allPages) => {
      return lastPage.length === 5 ? allPages.length * 5 : undefined;
    },
    initialPageParam: 0
  });
};

export default useThreads;
