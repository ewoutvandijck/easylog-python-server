import { useQuery } from '@tanstack/react-query';
import useApiClient from './use-api-client';

const useThreads = () => {
  const { threads, activeConnection } = useApiClient();
  return useQuery({
    queryKey: ['threads', activeConnection.name],
    queryFn: async () => {
      const response = await threads.getThreadsThreadsGet({
        limit: 100,
        order: 'desc'
      });

      return response.data;
    }
  });
};

export default useThreads;
