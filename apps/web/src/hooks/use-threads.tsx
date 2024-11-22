import { useQuery } from '@tanstack/react-query';
import useApiClient from './use-api-client';

const useThreads = () => {
  const { threads, activeConnection } = useApiClient();
  return useQuery({
    queryKey: ['threads', activeConnection.name],
    queryFn: () =>
      threads.getThreadsThreadsGet({
        limit: 100,
        order: 'desc'
      })
  });
};

export default useThreads;
