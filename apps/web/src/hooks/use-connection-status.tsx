import { useQuery } from '@tanstack/react-query';
import useConnections from './use-connections';

const useConnectionStatus = () => {
  const { activeConnection } = useConnections();

  return useQuery({
    queryKey: ['connection-status', activeConnection.name],
    queryFn: async () => {
      // HEALTH CHECK
    },
    refetchInterval: 1000
  });
};

export default useConnectionStatus;
