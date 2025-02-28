import { useQuery } from '@tanstack/react-query';

import useApiClient from './use-api-client';

const useIsConnectionHealthy = () => {
  const { health, activeConnection } = useApiClient();

  return useQuery({
    queryKey: ['connection-status', activeConnection.name],
    queryFn: async () => {
      try {
        const response = await health.healthHealthGet();
        return response.api === 'healthy' && response.main_db === 'healthy';
      } catch {
        return false;
      }
    },
    refetchInterval: (query) => (query.state.data ? 10000 : 1000)
  });
};

export default useIsConnectionHealthy;
