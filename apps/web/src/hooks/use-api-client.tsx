import createClient from '@/lib/api';
import useConnections from './use-connections';

import useConfigurations from './use-configurations';

const useApiClient = () => {
  const { activeConnection } = useConnections();
  const { activeConfiguration } = useConfigurations();

  const easylogApiKey = activeConfiguration?.easylogApiKey;

  const apiClient = createClient({
    basePath: activeConnection.url.replace(/\/$/, ''),
    apiKey: activeConnection.secret,
    accessToken: easylogApiKey || undefined
  });

  return { ...apiClient, activeConnection };
};

export default useApiClient;
