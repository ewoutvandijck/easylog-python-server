import { useQuery } from '@tanstack/react-query';
import useConnections from './use-connections';
import useApiClient from './use-api-client';

const useIsConnectionHealthy = () => {
  const { activeConnection } = useConnections();

  const apiClient = useApiClient();

  return useQuery({
    queryKey: ['connection-status', activeConnection.name],
    queryFn: async () => {
      try {
        const response = await apiClient.health.healthHealthGet();
        return response.status === 'healthy';
      } catch {
        return false;
      }
    },
    refetchInterval: 1000
  });
};

export default useIsConnectionHealthy;
