import { useQuery } from '@tanstack/react-query';

import useApiClient from './use-api-client';

const useIsConnectionHealthy = () => {
  const { health, activeConnection } = useApiClient();

  return useQuery({
    queryKey: ['connection-status', activeConnection.name],
    queryFn: async () => {
      try {
        const response = await health.healthHealthGet();
        return response.status === 'healthy';
      } catch {
        return false;
      }
    },
    refetchInterval: 1000
  });
};

export default useIsConnectionHealthy;
