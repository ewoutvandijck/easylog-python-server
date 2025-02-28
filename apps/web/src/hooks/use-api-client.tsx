import createClient from '@/lib/api';
import useConnections from './use-connections';
import { useMemo } from 'react';
import useConfigurations from './use-configurations';
import { HTTPHeaders } from '@/lib/api/generated-client';

const useApiClient = () => {
  const { activeConnection } = useConnections();
  const { activeConfiguration } = useConfigurations();

  return useMemo(() => {
    const easylogApiKey = activeConfiguration?.easylogApiKey || '';

    const headers: HTTPHeaders = easylogApiKey
      ? {
          Authorization: `Bearer ${easylogApiKey}`
        }
      : {};

    const apiClient = createClient({
      basePath: activeConnection.url,
      apiKey: activeConnection.secret,
      headers
    });

    return { ...apiClient, activeConnection };
  }, [activeConnection, activeConfiguration]);
};

export default useApiClient;
