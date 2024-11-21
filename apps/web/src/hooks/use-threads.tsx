import { useQuery } from '@tanstack/react-query';
import useApiClient from './use-api-client';

const useThreads = () => {
  const apiClient = useApiClient();
  return useQuery({
    queryKey: ['threads'],
    queryFn: () =>
      apiClient.threads.getThreadsThreadsGet({
        limit: 100
      })
  });
};

export default useThreads;
