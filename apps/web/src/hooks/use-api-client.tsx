import createClient from '@/lib/api';
import useConnections from './use-connections';
import { useMemo } from 'react';

const useApiClient = () => {
  const { activeConnection } = useConnections();

  return useMemo(() => {
    const apiClient = createClient({
      basePath: activeConnection.url,
      apiKey: activeConnection.secret
    });

    return apiClient;
  }, [activeConnection]);
};

export default useApiClient;
