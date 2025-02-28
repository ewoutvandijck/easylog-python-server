import createClient from '@/lib/api';
import useConnections from './use-connections';
import { useMemo } from 'react';
import useConfigurations from './use-configurations';

const useApiClient = () => {
  const { activeConnection } = useConnections();
  const { activeConfiguration } = useConfigurations();

  const easylogApiKey = activeConfiguration?.easylogApiKey;
  return useMemo(() => {
    const apiClient = createClient({
      basePath: activeConnection.url,
      apiKey: activeConnection.secret,
      accessToken: easylogApiKey || undefined
    });

    return { ...apiClient, activeConnection };
  }, [activeConnection, easylogApiKey]);
};

export default useApiClient;
